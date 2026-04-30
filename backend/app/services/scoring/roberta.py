"""RoBERTa-based sentiment scoring for Recombyne.

Heavy ML dependencies (`torch`, `transformers`) are imported lazily so the
rest of the codebase remains importable in lightweight environments such as
the CLI, tests for unrelated services, or build-only contexts.
"""

from __future__ import annotations

import asyncio
import logging
import math

import requests
from app.config import settings
from app.schemas.sentiment import SentimentResult
from app.services.scoring.base import BaseSentimentScorer
from app.services.scoring.text_preprocessor import ProcessedText, TextPreprocessor

logger = logging.getLogger(__name__)


def _torch():
    """Import torch lazily and return the module or None if unavailable."""

    try:
        import torch  # type: ignore

        return torch
    except Exception:
        return None


def _transformers():
    """Import transformers lazily and return the module or None."""

    try:
        from transformers import (  # type: ignore
            AutoModelForSequenceClassification,
            AutoTokenizer,
        )

        return AutoTokenizer, AutoModelForSequenceClassification
    except Exception:
        return None


class RoBERTaSentimentScorer(BaseSentimentScorer):
    """Sentiment scorer using cardiffnlp RoBERTa with API fallback."""

    _tokenizer = None
    _model = None
    _model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"

    def __init__(
        self,
        min_confidence: float = 0.55,
        preprocessor: TextPreprocessor | None = None,
    ) -> None:
        """Configure the scorer.

        Args:
            min_confidence: Threshold below which downstream consumers should
                soft-downweight the post rather than reject it.
            preprocessor: Optional preprocessor injected for testing.
        """

        self._min_confidence = float(min_confidence)
        self._preprocessor = preprocessor or TextPreprocessor()

    def is_model_ready(self) -> bool:
        """Report whether a model is currently loaded in memory."""

        return bool(self._model and self._tokenizer)

    @property
    def min_confidence(self) -> float:
        """Expose the minimum confidence threshold."""

        return self._min_confidence

    async def _ensure_model(self) -> None:
        """Load the model and tokenizer lazily once per process."""

        if self._model and self._tokenizer:
            return
        loaders = _transformers()
        if loaders is None:
            return
        AutoTokenizer, AutoModelForSequenceClassification = loaders
        try:
            self.__class__._tokenizer = await asyncio.to_thread(
                AutoTokenizer.from_pretrained, self._model_name
            )
            self.__class__._model = await asyncio.to_thread(
                AutoModelForSequenceClassification.from_pretrained, self._model_name
            )
        except Exception as exc:
            logger.warning(
                "Local RoBERTa load failed; using HF inference fallback. reason=%s",
                exc,
            )
            self.__class__._tokenizer = None
            self.__class__._model = None

    @staticmethod
    def _softmax(logits: list[float]) -> list[float]:
        """Pure-Python softmax fallback used when torch is unavailable."""

        if not logits:
            return []
        max_value = max(logits)
        exps = [math.exp(x - max_value) for x in logits]
        total = sum(exps)
        if total <= 0:
            return [1.0 / len(logits)] * len(logits)
        return [value / total for value in exps]

    @staticmethod
    def _normalize_logits(
        logits: list[float], processed: ProcessedText | None = None
    ) -> SentimentResult:
        """Convert model logits into Recombyne sentiment coordinates."""

        torch = _torch()
        if torch is not None:
            tensor = torch.tensor(logits, dtype=torch.float32)
            probs = torch.softmax(tensor, dim=-1).tolist()
            label_index = int(torch.argmax(tensor).item())
        else:
            probs = RoBERTaSentimentScorer._softmax(logits)
            label_index = int(probs.index(max(probs))) if probs else 1

        labels = ["negative", "neutral", "positive"]
        label = labels[label_index]
        confidence = float(probs[label_index]) if probs else 0.0
        label_to_anchor = {"negative": -1.0, "neutral": 0.0, "positive": 1.0}

        modifier = processed.confidence_modifier if processed else 1.0
        adjusted_confidence = max(0.0, min(1.0, confidence * modifier))
        score = label_to_anchor[label] * adjusted_confidence

        return SentimentResult(
            label=label,
            score=score,
            confidence=adjusted_confidence,
            raw_logits=logits,
            negation_detected=processed.negation_detected if processed else False,
            sarcasm_risk=processed.sarcasm_risk if processed else 0.0,
            is_english=processed.language.is_english if processed else True,
        )

    def _prepare(self, text: str) -> ProcessedText:
        """Run the shared preprocessor for a single text input."""

        return self._preprocessor.preprocess(text)

    async def _score_via_local_model(
        self, processed: ProcessedText
    ) -> SentimentResult | None:
        """Score processed text using locally loaded model if available."""

        torch = _torch()
        if torch is None:
            return None
        await self._ensure_model()
        if not self._model or not self._tokenizer:
            return None
        encoded = self._tokenizer(
            processed.cleaned_text or " ",
            return_tensors="pt",
            truncation=True,
            max_length=256,
        )
        with torch.no_grad():
            output = self._model(**encoded)
        return self._normalize_logits(output.logits[0].tolist(), processed)

    async def _score_via_hf_api(self, processed: ProcessedText) -> SentimentResult:
        """Fallback scorer using Hugging Face Inference API."""

        if not settings.huggingface_api_key:
            raise RuntimeError(
                "Local model unavailable and HUGGINGFACE_API_KEY is not configured."
            )
        headers = {"Authorization": f"Bearer {settings.huggingface_api_key}"}
        payload = {"inputs": processed.cleaned_text or " "}
        url = f"https://api-inference.huggingface.co/models/{self._model_name}"
        response = await asyncio.to_thread(
            requests.post, url, headers=headers, json=payload, timeout=30
        )
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list) and data and isinstance(data[0], list):
            entries = data[0]
            score_map = {
                entry["label"].lower(): float(entry["score"]) for entry in entries
            }
            logits = [
                score_map.get("negative", 0.0),
                score_map.get("neutral", 0.0),
                score_map.get("positive", 0.0),
            ]
            return self._normalize_logits(logits, processed)
        raise RuntimeError("Unexpected Hugging Face inference API response format.")

    async def score(self, text: str) -> SentimentResult:
        """Score a single text sample using local model with API fallback."""

        processed = self._prepare(text)
        local = await self._score_via_local_model(processed)
        if local is not None:
            return local
        return await self._score_via_hf_api(processed)

    async def batch_score(self, texts: list[str]) -> list[SentimentResult]:
        """Score multiple texts with one model pass when possible."""

        processed_batch = [self._prepare(text) for text in texts]
        torch = _torch()
        if torch is not None:
            await self._ensure_model()
        if torch is not None and self._model and self._tokenizer:
            encoded = self._tokenizer(
                [p.cleaned_text or " " for p in processed_batch],
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=256,
            )
            with torch.no_grad():
                output = self._model(**encoded)
            return [
                self._normalize_logits(row.tolist(), processed)
                for row, processed in zip(output.logits, processed_batch, strict=True)
            ]
        return [
            await self._score_via_hf_api(processed) for processed in processed_batch
        ]

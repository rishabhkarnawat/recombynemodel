"""RoBERTa-based sentiment scoring for Recombyne."""

from __future__ import annotations

import asyncio
import logging

import requests
import torch
from app.config import settings
from app.schemas.sentiment import SentimentResult
from app.services.scoring.base import BaseSentimentScorer
from transformers import AutoModelForSequenceClassification, AutoTokenizer

logger = logging.getLogger(__name__)


class RoBERTaSentimentScorer(BaseSentimentScorer):
    """Sentiment scorer using cardiffnlp RoBERTa with API fallback."""

    _tokenizer = None
    _model = None
    _model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"

    def is_model_ready(self) -> bool:
        """Report whether a model is currently loaded in memory."""

        return bool(self._model and self._tokenizer)

    async def _ensure_model(self) -> None:
        """Load the model and tokenizer lazily once per process."""

        if self._model and self._tokenizer:
            return
        try:
            self.__class__._tokenizer = await asyncio.to_thread(
                AutoTokenizer.from_pretrained, self._model_name
            )
            self.__class__._model = await asyncio.to_thread(
                AutoModelForSequenceClassification.from_pretrained, self._model_name
            )
        except Exception as exc:
            logger.warning(
                "Local RoBERTa load failed; using HF inference fallback. reason=%s", exc
            )
            self.__class__._tokenizer = None
            self.__class__._model = None

    @staticmethod
    def _normalize_logits(logits: list[float]) -> SentimentResult:
        """Convert model logits into Recombyne sentiment coordinates."""

        tensor = torch.tensor(logits, dtype=torch.float32)
        probs = torch.softmax(tensor, dim=-1).tolist()
        label_index = int(torch.argmax(tensor).item())
        labels = ["negative", "neutral", "positive"]
        label = labels[label_index]
        confidence = float(probs[label_index])
        label_to_anchor = {"negative": -1.0, "neutral": 0.0, "positive": 1.0}
        score = label_to_anchor[label] * confidence
        return SentimentResult(
            label=label, score=score, confidence=confidence, raw_logits=logits
        )

    async def _score_via_local_model(self, text: str) -> SentimentResult | None:
        """Score text using locally loaded model if available."""

        await self._ensure_model()
        if not self._model or not self._tokenizer:
            return None
        encoded = self._tokenizer(
            text, return_tensors="pt", truncation=True, max_length=256
        )
        with torch.no_grad():
            output = self._model(**encoded)
        return self._normalize_logits(output.logits[0].tolist())

    async def _score_via_hf_api(self, text: str) -> SentimentResult:
        """Fallback scorer using Hugging Face Inference API."""

        if not settings.huggingface_api_key:
            raise RuntimeError(
                "Local model unavailable and HUGGINGFACE_API_KEY is not configured."
            )
        headers = {"Authorization": f"Bearer {settings.huggingface_api_key}"}
        payload = {"inputs": text}
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
            return self._normalize_logits(logits)
        raise RuntimeError("Unexpected Hugging Face inference API response format.")

    async def score(self, text: str) -> SentimentResult:
        """Score a single text sample using local model with API fallback."""

        local = await self._score_via_local_model(text)
        if local is not None:
            return local
        return await self._score_via_hf_api(text)

    async def batch_score(self, texts: list[str]) -> list[SentimentResult]:
        """Score multiple texts with one model pass when possible."""

        await self._ensure_model()
        if self._model and self._tokenizer:
            encoded = self._tokenizer(
                texts,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=256,
            )
            with torch.no_grad():
                output = self._model(**encoded)
            return [self._normalize_logits(row.tolist()) for row in output.logits]
        return [await self._score_via_hf_api(text) for text in texts]

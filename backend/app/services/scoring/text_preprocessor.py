"""Text preprocessing for the Recombyne sentiment pipeline.

Provides cleaning, negation detection, sarcasm risk estimation, and language
identification used to enrich and adjust sentiment scoring confidence before
posts reach the RoBERTa model.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field

try:  # pragma: no cover - optional dependency import guard
    from langdetect import DetectorFactory, detect_langs

    DetectorFactory.seed = 0
    _LANGDETECT_AVAILABLE = True
except Exception:  # pragma: no cover
    _LANGDETECT_AVAILABLE = False


_NEGATION_TOKENS = {
    "not",
    "never",
    "no",
    "dont",
    "don't",
    "isnt",
    "isn't",
    "wasnt",
    "wasn't",
    "cant",
    "can't",
    "wont",
    "won't",
    "doesnt",
    "doesn't",
    "couldnt",
    "couldn't",
    "shouldnt",
    "shouldn't",
}

_SENTIMENT_TOKENS = {
    "good",
    "great",
    "awesome",
    "amazing",
    "love",
    "perfect",
    "happy",
    "excellent",
    "bad",
    "terrible",
    "awful",
    "hate",
    "broken",
    "worst",
    "horrible",
    "disappointing",
    "scam",
    "useless",
}

_SARCASM_MARKERS = (
    "yeah right",
    "sure",
    "totally",
    "great job",
    "wow thanks",
    "absolutely",
    "love how",
    "as if",
    "what a surprise",
)

_NEGATIVE_CONTEXT = {
    "broken",
    "fail",
    "failed",
    "scam",
    "bug",
    "crash",
    "down",
    "dead",
    "trash",
    "useless",
    "lost",
    "delay",
    "slow",
    "rip",
    "lol",
    "lmao",
}


class LanguageResult(BaseModel):
    """Language detection result for a piece of text."""

    language: str
    confidence: float = Field(ge=0.0, le=1.0)
    is_english: bool


class ProcessedText(BaseModel):
    """Output from the preprocessing pipeline used by the scoring layer."""

    cleaned_text: str
    negation_detected: bool
    sarcasm_risk: float = Field(ge=0.0, le=1.0)
    confidence_modifier: float = Field(ge=0.0, le=1.0)
    language: LanguageResult


class TextPreprocessor:
    """Apply lightweight text cleaning and confidence-modifying heuristics."""

    def __init__(self, primary_topic: str | None = None) -> None:
        """Configure the preprocessor.

        Args:
            primary_topic: Optional topic mention preserved during cleaning so
                that mentions of the queried topic remain in the input text.
        """

        self._primary_topic = (primary_topic or "").lower().strip()

    def detect_language(self, text: str) -> LanguageResult:
        """Detect the dominant language of a text sample.

        Args:
            text: Raw text to analyze.

        Returns:
            LanguageResult describing detected language and confidence.
        """

        if not text or not _LANGDETECT_AVAILABLE:
            return LanguageResult(language="unknown", confidence=0.0, is_english=False)
        try:
            detections = detect_langs(text)
        except Exception:
            return LanguageResult(language="unknown", confidence=0.0, is_english=False)
        if not detections:
            return LanguageResult(language="unknown", confidence=0.0, is_english=False)
        top = detections[0]
        is_english = top.lang == "en" and top.prob > 0.85
        return LanguageResult(
            language=top.lang, confidence=float(top.prob), is_english=is_english
        )

    def _clean(self, text: str) -> str:
        """Strip URLs, normalize hashtags/mentions, and collapse whitespace.

        Args:
            text: Raw text input.

        Returns:
            Cleaned text safe to feed into the scorer.
        """

        cleaned = re.sub(r"https?://\S+", " ", text)

        def _mention_replacer(match: re.Match[str]) -> str:
            handle = match.group(1).lower()
            if self._primary_topic and self._primary_topic.lstrip("@") in handle:
                return match.group(0)
            return " "

        cleaned = re.sub(r"@(\w+)", _mention_replacer, cleaned)
        cleaned = re.sub(r"#(\w+)", r"\1", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    @staticmethod
    def _detect_negation(tokens: list[str]) -> bool:
        """Detect a negation token within five tokens of a sentiment token.

        Args:
            tokens: Lowercase tokens of the cleaned text.

        Returns:
            True when negation likely flips sentiment intent.
        """

        for index, token in enumerate(tokens):
            if token in _NEGATION_TOKENS:
                window = tokens[index + 1 : index + 6]
                if any(candidate in _SENTIMENT_TOKENS for candidate in window):
                    return True
        return False

    @staticmethod
    def _sarcasm_risk(text_lower: str, tokens: list[str]) -> float:
        """Estimate sarcasm risk using marker phrases and contrast cues.

        Args:
            text_lower: Lowercase cleaned text.
            tokens: Token list for proximity checks.

        Returns:
            Sarcasm risk score in the range 0.0 - 1.0.
        """

        risk = 0.0
        if any(marker in text_lower for marker in _SARCASM_MARKERS):
            risk += 0.4
        if "!" in text_lower and any(token in _NEGATIVE_CONTEXT for token in tokens):
            risk += 0.3
        positive_then_negative = re.search(
            r"(amazing|great|love|perfect|awesome|wonderful)[^\.!\?]{0,40}(broken|fail|scam|crash|delay|down)",
            text_lower,
        )
        if positive_then_negative:
            risk += 0.3
        return float(min(1.0, risk))

    def preprocess(self, text: str) -> ProcessedText:
        """Run the full preprocessing pipeline.

        Args:
            text: Raw post text.

        Returns:
            ProcessedText with cleaned text and confidence modifiers applied.
        """

        cleaned = self._clean(text)
        lower = cleaned.lower()
        tokens = re.findall(r"[a-zA-Z']+", lower)
        negation_detected = self._detect_negation(tokens)
        sarcasm_risk = self._sarcasm_risk(lower, tokens)

        confidence_modifier = 1.0
        if negation_detected:
            confidence_modifier = min(confidence_modifier, 0.75)
        if sarcasm_risk > 0.6:
            confidence_modifier = min(confidence_modifier, 0.60)

        language = self.detect_language(cleaned or text)
        if not language.is_english:
            confidence_modifier = min(confidence_modifier, 0.50)

        return ProcessedText(
            cleaned_text=cleaned,
            negation_detected=negation_detected,
            sarcasm_risk=sarcasm_risk,
            confidence_modifier=confidence_modifier,
            language=language,
        )


__all__: list[str] = [
    "LanguageResult",
    "ProcessedText",
    "TextPreprocessor",
]


SeverityLevel = Literal["low", "medium", "high"]

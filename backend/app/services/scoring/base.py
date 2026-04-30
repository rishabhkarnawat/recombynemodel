"""Abstract interfaces for sentiment scoring services."""

from abc import ABC, abstractmethod

from app.schemas.sentiment import SentimentResult


class BaseSentimentScorer(ABC):
    """Contract for sentiment scoring engines."""

    @abstractmethod
    async def score(self, text: str) -> SentimentResult:
        """Score a single text entry."""

    @abstractmethod
    async def batch_score(self, texts: list[str]) -> list[SentimentResult]:
        """Score a batch of texts efficiently."""

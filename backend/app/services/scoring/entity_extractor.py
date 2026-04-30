"""Entity co-mention extraction for Recombyne."""

from __future__ import annotations

import logging
import re
from collections import defaultdict

from app.schemas.sentiment import CoMention, SentimentResult
from app.services.ingestion.base import RawPost

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    import spacy

    _SPACY_AVAILABLE = True
except Exception:  # pragma: no cover
    spacy = None  # type: ignore[assignment]
    _SPACY_AVAILABLE = False


_NLP = None
_FALLBACK_TOKEN_RE = re.compile(r"\b([A-Z][a-zA-Z0-9]{2,}(?:\s+[A-Z][a-zA-Z0-9]+)*)\b")


def _load_spacy_model():
    """Lazily load the spaCy small English model with a friendly fallback."""

    global _NLP
    if not _SPACY_AVAILABLE or spacy is None:
        return None
    if _NLP is not None:
        return _NLP
    try:
        _NLP = spacy.load("en_core_web_sm")
    except Exception as exc:  # pragma: no cover
        logger.warning(
            "spaCy model not available; falling back to regex. reason=%s", exc
        )
        _NLP = None
    return _NLP


class EntityExtractor:
    """Extract co-mentioned entities from a batch of posts."""

    def __init__(self, max_results: int = 10) -> None:
        """Configure the extractor.

        Args:
            max_results: Maximum number of co-mentions to return.
        """

        self._max_results = int(max_results)

    def _extract_entities(self, text: str) -> list[str]:
        """Return candidate entities for a single post."""

        nlp = _load_spacy_model()
        if nlp is not None:
            doc = nlp(text)
            return [
                ent.text.strip()
                for ent in doc.ents
                if ent.label_ in {"ORG", "PRODUCT", "PERSON", "GPE", "EVENT"}
            ]
        return [match.group(1).strip() for match in _FALLBACK_TOKEN_RE.finditer(text)]

    def extract(
        self,
        posts: list[RawPost],
        sentiments: list[SentimentResult],
        primary_topic: str,
    ) -> list[CoMention]:
        """Compute co-mention metrics for the queried topic.

        Args:
            posts: Raw posts in the batch.
            sentiments: Sentiment outputs aligned to posts.
            primary_topic: Topic being queried; excluded from results.

        Returns:
            Up to ``max_results`` CoMention entries sorted by weighted count.
        """

        if not posts or not sentiments or len(posts) != len(sentiments):
            return []

        primary_lower = primary_topic.strip().lower()
        mention_counts: dict[str, int] = defaultdict(int)
        weighted_counts: dict[str, float] = defaultdict(float)
        sentiment_sums: dict[str, float] = defaultdict(float)
        sentiment_observations: dict[str, int] = defaultdict(int)

        for post, sentiment in zip(posts, sentiments, strict=True):
            entities = self._extract_entities(post.text)
            seen_for_post: set[str] = set()
            for entity in entities:
                normalized = entity.strip()
                key = normalized.lower()
                if not normalized or len(normalized) < 2:
                    continue
                if key == primary_lower or primary_lower in key:
                    continue
                if key in seen_for_post:
                    continue
                seen_for_post.add(key)
                mention_counts[normalized] += 1
                weight = max(
                    0.0, post.raw_engagement.likes + post.raw_engagement.comments
                )
                weighted_counts[normalized] += float(1.0 + weight)
                sentiment_sums[normalized] += sentiment.score
                sentiment_observations[normalized] += 1

        results: list[CoMention] = []
        for entity, count in mention_counts.items():
            observations = sentiment_observations[entity]
            avg_sentiment = (
                sentiment_sums[entity] / observations if observations else 0.0
            )
            if avg_sentiment > 0.10:
                direction = "positive_association"
            elif avg_sentiment < -0.10:
                direction = "negative_association"
            else:
                direction = "neutral"
            results.append(
                CoMention(
                    entity=entity,
                    mention_count=count,
                    weighted_mention_count=weighted_counts[entity],
                    avg_sentiment_when_mentioned=avg_sentiment,
                    sentiment_direction=direction,
                )
            )

        results.sort(key=lambda item: item.weighted_mention_count, reverse=True)
        return results[: self._max_results]


__all__: list[str] = ["EntityExtractor"]

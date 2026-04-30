"""Engagement weighting logic for Recombyne sentiment intelligence.

This module is the core of the platform. It produces engagement-weighted
sentiment outputs from raw posts and per-post sentiment scores. The pipeline
combines four ideas:

1. Raw engagement scoring per platform.
2. Logarithmic normalization to prevent viral outliers from dominating.
3. Time decay so recent posts contribute more signal than old posts.
4. Optional author credibility weighting normalized across the batch.

A viral post from five days ago is historical record, not current signal.
Recombyne trades in what is moving now, which is why time decay matters.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

from app.schemas.sentiment import SentimentResult, TopSignal, WeightedResult
from app.services.ingestion.base import RawPost
from app.services.scoring.author_scorer import AuthorScorer

DEFAULT_DECAY_RATE = 0.05
DEFAULT_MIN_CONFIDENCE = 0.55


class EngagementWeighter:
    """Apply platform-specific engagement weighting to sentiment outputs."""

    def __init__(
        self,
        decay_rate: float = DEFAULT_DECAY_RATE,
        use_author_scoring: bool = True,
        min_confidence: float = DEFAULT_MIN_CONFIDENCE,
        now: datetime | None = None,
    ) -> None:
        """Configure weighting behavior.

        Args:
            decay_rate: Lambda for the exponential time decay multiplier.
            use_author_scoring: When True, integrate author credibility weights.
            min_confidence: Threshold below which low-confidence posts are
                softly downweighted instead of dropped.
            now: Optional reference time for deterministic testing.
        """

        self._decay_rate = float(decay_rate)
        self._use_author_scoring = bool(use_author_scoring)
        self._min_confidence = float(min_confidence)
        self._now = now or datetime.now(timezone.utc)
        self._author_scorer = AuthorScorer() if self._use_author_scoring else None

    def _compute_decay(self, post: RawPost) -> float:
        """Compute the time-decay multiplier for a single post.

        Args:
            post: Raw post containing the original publication timestamp.

        Returns:
            Decay multiplier in the range (0, 1].
        """

        created_at = post.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        delta_hours = max(0.0, (self._now - created_at).total_seconds() / 3600.0)
        return math.exp(-self._decay_rate * delta_hours)

    def compute_weight(self, post: RawPost, author_weight: float = 1.0) -> float:
        """Compute the final engagement weight for a single post.

        Args:
            post: Raw post under evaluation.
            author_weight: Pre-normalized author credibility multiplier.

        Returns:
            Final non-negative weight combining engagement, decay, and author.
        """

        engagement = post.raw_engagement
        if post.source == "twitter":
            raw_score = (
                (engagement.likes * 1.0)
                + (engagement.reposts * 2.5)
                + (engagement.comments * 1.5)
                + ((engagement.views * 0.01) if engagement.views else 0.0)
            )
        else:
            raw_score = (
                (engagement.likes * 1.0)
                + (engagement.comments * 2.0)
                + (
                    (engagement.upvote_ratio * 100.0)
                    if engagement.upvote_ratio is not None
                    else 50.0
                )
            )

        decay = self._compute_decay(post)
        normalized = math.log(1.0 + max(0.0, raw_score))
        return normalized * decay * max(0.0, author_weight)

    def _build_author_weights(self, posts: list[RawPost]) -> list[float]:
        """Compute per-post normalized author weights for the batch.

        Args:
            posts: Posts being weighted.

        Returns:
            List of author multipliers aligned with posts (defaults to 1.0).
        """

        if not self._use_author_scoring or not self._author_scorer:
            return [1.0 for _ in posts]

        raw_weights: list[float] = []
        for post in posts:
            metrics = post.author_metrics.model_dump() if post.author_metrics else {}
            if post.source == "twitter":
                raw_weights.append(self._author_scorer.score_twitter_author(metrics))
            else:
                raw_weights.append(self._author_scorer.score_reddit_author(metrics))
        return self._author_scorer.normalize_batch(raw_weights)

    def apply_weights(
        self, posts: list[RawPost], sentiments: list[SentimentResult]
    ) -> WeightedResult:
        """Aggregate raw and weighted sentiment scores with divergence outputs.

        Args:
            posts: Raw posts in the same order as sentiments.
            sentiments: Sentiment results aligned to posts.

        Returns:
            WeightedResult containing weighted aggregates, top signals, and
            quality counters used by the dashboard and CLI surfaces.
        """

        if not posts or not sentiments or len(posts) != len(sentiments):
            return WeightedResult(
                raw_score=0.0,
                weighted_score=0.0,
                total_posts=0,
                total_weighted_posts=0.0,
                divergence=0.0,
                divergence_flag=False,
                divergence_direction="aligned",
                top_signals=[],
                low_confidence_post_count=0,
                non_english_post_count=0,
            )

        raw_score = sum(item.score for item in sentiments) / len(sentiments)

        author_weights = self._build_author_weights(posts)
        base_weights = [
            self.compute_weight(post, author_weight=author_weight)
            for post, author_weight in zip(posts, author_weights, strict=True)
        ]

        adjusted_weights: list[float] = []
        low_confidence_count = 0
        non_english_count = 0
        for sentiment, weight in zip(sentiments, base_weights, strict=True):
            adjusted = weight
            if sentiment.confidence < self._min_confidence and self._min_confidence > 0:
                adjusted = adjusted * (sentiment.confidence / self._min_confidence)
                low_confidence_count += 1
            if not sentiment.is_english:
                non_english_count += 1
            adjusted_weights.append(adjusted)

        total_weight = sum(adjusted_weights)
        weighted_score = 0.0
        if total_weight > 0:
            weighted_score = (
                sum(
                    sentiment.score * weight
                    for sentiment, weight in zip(
                        sentiments, adjusted_weights, strict=True
                    )
                )
                / total_weight
            )

        divergence = weighted_score - raw_score
        if divergence > 0.15:
            direction = "weighted_positive"
        elif divergence < -0.15:
            direction = "weighted_negative"
        else:
            direction = "aligned"

        top_signals = sorted(
            [
                TopSignal(
                    post=post,
                    sentiment=sentiment,
                    weight=weight,
                    signal_strength=weight * abs(sentiment.score),
                )
                for post, sentiment, weight in zip(
                    posts, sentiments, adjusted_weights, strict=True
                )
            ],
            key=lambda item: item.signal_strength,
            reverse=True,
        )[:5]

        return WeightedResult(
            raw_score=raw_score,
            weighted_score=weighted_score,
            total_posts=len(posts),
            total_weighted_posts=total_weight,
            divergence=divergence,
            divergence_flag=abs(divergence) > 0.15,
            divergence_direction=direction,
            top_signals=top_signals,
            low_confidence_post_count=low_confidence_count,
            non_english_post_count=non_english_count,
        )

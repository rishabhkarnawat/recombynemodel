"""Divergence detection helpers for Recombyne."""

from __future__ import annotations

from collections import Counter
from typing import Iterable

from app.schemas.sentiment import DivergenceFlag, SentimentResult, WeightedResult
from app.services.ingestion.base import RawPost


class DivergenceDetector:
    """Detect and explain divergence patterns across sentiment views."""

    def build_explanations(
        self,
        weighted_result: WeightedResult,
        twitter_score: float | None = None,
        reddit_score: float | None = None,
        prior_window_score: float | None = None,
    ) -> list[str]:
        """Generate human-readable divergence explanations."""

        flags: list[str] = []
        if weighted_result.divergence_flag:
            if weighted_result.divergence_direction == "weighted_positive":
                flags.append(
                    "High-engagement voices are significantly more positive than the overall conversation. Enthusiasm is concentrated among influential voices."
                )
            elif weighted_result.divergence_direction == "weighted_negative":
                flags.append(
                    "High-engagement voices are significantly more negative than the overall conversation. Concern is concentrated among influential voices."
                )
        if (
            twitter_score is not None
            and reddit_score is not None
            and abs(twitter_score - reddit_score) > 0.20
        ):
            flags.append(
                "Twitter and Reddit sentiment diverge materially for this topic. Community context may be driving source-specific narratives."
            )
        if (
            prior_window_score is not None
            and abs(weighted_result.weighted_score - prior_window_score) > 0.20
        ):
            flags.append(
                "Current sentiment shifted sharply compared with the prior window. Momentum or a new catalyst may be changing the narrative."
            )
        return flags

    def build_structured_flags(
        self,
        weighted_result: WeightedResult,
        posts: Iterable[RawPost],
        sentiments: Iterable[SentimentResult],
    ) -> list[DivergenceFlag]:
        """Produce structured flags for the four supported divergence types.

        Args:
            weighted_result: Aggregate weighted output for the query window.
            posts: Raw posts aligned to the sentiment list.
            sentiments: Sentiment results aligned to posts.

        Returns:
            List of DivergenceFlag entries describing each detected pattern.
        """

        post_list = list(posts)
        sentiment_list = list(sentiments)
        flags: list[DivergenceFlag] = []

        flags.extend(self._weighted_vs_raw(weighted_result))
        flags.extend(self._platform_divergence(post_list, sentiment_list))
        flags.extend(self._temporal_divergence(post_list, sentiment_list))
        flags.extend(self._volume_divergence(post_list))
        return flags

    @staticmethod
    def _severity(magnitude: float, low: float, medium: float) -> str:
        """Classify divergence severity bands.

        Args:
            magnitude: Absolute divergence magnitude.
            low: Lower bound for the medium band.
            medium: Lower bound for the high band.

        Returns:
            Severity label string.
        """

        if magnitude >= medium:
            return "high"
        if magnitude >= low:
            return "medium"
        return "low"

    def _weighted_vs_raw(self, weighted_result: WeightedResult) -> list[DivergenceFlag]:
        """Build a structured flag for the existing weighted-vs-raw signal."""

        if not weighted_result.divergence_flag:
            return []
        magnitude = abs(weighted_result.divergence)
        explanation = (
            "High-engagement voices skew positive relative to the overall conversation."
            if weighted_result.divergence_direction == "weighted_positive"
            else "High-engagement voices skew negative relative to the overall conversation."
        )
        return [
            DivergenceFlag(
                type="weighted_vs_raw",
                severity=self._severity(magnitude, 0.15, 0.35),
                explanation=explanation,
            )
        ]

    @staticmethod
    def _safe_mean(values: list[float]) -> float:
        """Return mean of values or zero for empty input."""

        return sum(values) / len(values) if values else 0.0

    def _platform_divergence(
        self, posts: list[RawPost], sentiments: list[SentimentResult]
    ) -> list[DivergenceFlag]:
        """Detect significant Twitter vs Reddit weighted score gaps."""

        twitter_scores = [
            sentiment.score
            for post, sentiment in zip(posts, sentiments, strict=True)
            if post.source == "twitter"
        ]
        reddit_scores = [
            sentiment.score
            for post, sentiment in zip(posts, sentiments, strict=True)
            if post.source == "reddit"
        ]
        if not twitter_scores or not reddit_scores:
            return []

        tw_score = self._safe_mean(twitter_scores)
        rd_score = self._safe_mean(reddit_scores)
        delta = tw_score - rd_score
        if abs(delta) <= 0.20:
            return []
        explanation = (
            f"Twitter sentiment ({tw_score:+.2f}) is significantly more positive than "
            f"Reddit sentiment ({rd_score:+.2f}). Opinion leaders and retail audiences are split."
            if delta > 0
            else f"Reddit sentiment ({rd_score:+.2f}) is significantly more positive than "
            f"Twitter sentiment ({tw_score:+.2f}). Community context may be diverging from the broader conversation."
        )
        return [
            DivergenceFlag(
                type="platform",
                severity=self._severity(abs(delta), 0.20, 0.40),
                explanation=explanation,
            )
        ]

    def _temporal_divergence(
        self, posts: list[RawPost], sentiments: list[SentimentResult]
    ) -> list[DivergenceFlag]:
        """Compare oldest 20% vs most recent 20% of posts."""

        if len(posts) < 5:
            return []
        ordered = sorted(
            zip(posts, sentiments, strict=True), key=lambda item: item[0].created_at
        )
        bucket_size = max(1, len(ordered) // 5)
        oldest = ordered[:bucket_size]
        newest = ordered[-bucket_size:]
        old_mean = self._safe_mean([sentiment.score for _, sentiment in oldest])
        new_mean = self._safe_mean([sentiment.score for _, sentiment in newest])
        delta = new_mean - old_mean
        if abs(delta) <= 0.25:
            return []
        explanation = (
            "Sentiment has shifted sharply in the last 24 hours. Early conversation was "
            "negative; recent posts are turning positive."
            if delta > 0
            else "Sentiment has shifted sharply in the last 24 hours. Early conversation was "
            "positive; recent posts are turning negative."
        )
        return [
            DivergenceFlag(
                type="temporal",
                severity=self._severity(abs(delta), 0.25, 0.50),
                explanation=explanation,
            )
        ]

    def _volume_divergence(self, posts: list[RawPost]) -> list[DivergenceFlag]:
        """Detect a >3x volume spike in any single hour vs the baseline."""

        if not posts:
            return []
        hour_counts: Counter[str] = Counter()
        for post in posts:
            bucket = post.created_at.replace(minute=0, second=0, microsecond=0)
            hour_counts[bucket.isoformat()] += 1

        counts = list(hour_counts.values())
        if len(counts) < 2:
            return []
        baseline = max(1.0, sum(counts) / len(counts))
        max_hour = max(counts)
        ratio = max_hour / baseline
        if ratio < 3.0:
            return []

        explanation = (
            f"Post volume spiked {ratio:.1f}x in the last hour. A significant event may be "
            "driving conversation. Sentiment readings during volume spikes should be "
            "interpreted with caution."
        )
        return [
            DivergenceFlag(
                type="volume",
                severity=self._severity(ratio, 3.0, 5.0),
                explanation=explanation,
            )
        ]


__all__: list[str] = ["DivergenceDetector"]

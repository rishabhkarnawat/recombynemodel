"""Timeline aggregation service for Recombyne."""

from collections import Counter, defaultdict
from datetime import datetime
from typing import Literal

from app.schemas.sentiment import (SentimentResult, TimelineBucket,
                                   TimelineResult)
from app.services.ingestion.base import RawPost
from app.services.scoring.engagement_weighter import EngagementWeighter


class TimelineAggregator:
    """Build time-bucketed sentiment timelines and trend direction."""

    def build_timeline(
        self,
        posts: list[RawPost],
        sentiments: list[SentimentResult],
        bucket: Literal["hour", "day"] = "hour",
    ) -> TimelineResult:
        """Aggregate timeline buckets and compute trend direction."""

        grouped: dict[datetime, list[tuple[RawPost, SentimentResult]]] = defaultdict(
            list
        )
        for post, sentiment in zip(posts, sentiments, strict=True):
            key = (
                post.created_at.replace(hour=0, minute=0, second=0, microsecond=0)
                if bucket == "day"
                else post.created_at.replace(minute=0, second=0, microsecond=0)
            )
            grouped[key].append((post, sentiment))

        weighter = EngagementWeighter()
        buckets: list[TimelineBucket] = []
        for timestamp in sorted(grouped.keys()):
            entries = grouped[timestamp]
            post_batch = [entry[0] for entry in entries]
            sentiment_batch = [entry[1] for entry in entries]
            weighted = weighter.apply_weights(post_batch, sentiment_batch)
            dominant = Counter(item.label for item in sentiment_batch).most_common(1)[
                0
            ][0]
            buckets.append(
                TimelineBucket(
                    timestamp=timestamp,
                    raw_score=weighted.raw_score,
                    weighted_score=weighted.weighted_score,
                    post_count=len(post_batch),
                    dominant_label=dominant,
                )
            )

        return TimelineResult(
            buckets=buckets, trend_direction=self._compute_trend_direction(buckets)
        )

    def _compute_trend_direction(
        self, buckets: list[TimelineBucket]
    ) -> Literal["surging", "rising", "flat", "falling", "crashing"]:
        """Compute trend direction comparing first, midpoint, and last buckets."""

        if len(buckets) < 2:
            return "flat"
        first = buckets[0].weighted_score
        mid = buckets[len(buckets) // 2].weighted_score
        last = buckets[-1].weighted_score
        delta = ((last - first) + (last - mid)) / 2
        if delta > 0.30:
            return "surging"
        if delta > 0.10:
            return "rising"
        if delta < -0.30:
            return "crashing"
        if delta < -0.10:
            return "falling"
        return "flat"

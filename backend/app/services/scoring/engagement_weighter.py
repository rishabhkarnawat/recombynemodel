"""Engagement weighting logic for Recombyne sentiment intelligence."""

import math

from app.schemas.sentiment import SentimentResult, TopSignal, WeightedResult
from app.services.ingestion.base import RawPost


class EngagementWeighter:
    """Apply platform-specific engagement weighting to sentiment outputs."""

    def compute_weight(self, post: RawPost) -> float:
        """Compute engagement weight for a post using platform-specific formula."""

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
        return math.log(1.0 + raw_score)

    def apply_weights(
        self, posts: list[RawPost], sentiments: list[SentimentResult]
    ) -> WeightedResult:
        """Aggregate raw and weighted sentiment scores with divergence outputs."""

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
            )

        raw_score = sum(item.score for item in sentiments) / len(sentiments)
        weights = [self.compute_weight(post) for post in posts]
        total_weight = sum(weights)
        weighted_score = 0.0
        if total_weight > 0:
            weighted_score = (
                sum(
                    sentiment.score * weight
                    for sentiment, weight in zip(sentiments, weights, strict=True)
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
                    posts, sentiments, weights, strict=True
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
        )

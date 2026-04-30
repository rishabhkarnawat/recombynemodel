"""Author credibility scoring for Recombyne engagement weighting.

Computes per-author multipliers used by the engagement weighter so that
high-credibility authors contribute proportionally more signal. Multipliers
are min-max normalized across the batch into a stable [0.5, 2.0] range.
"""

from __future__ import annotations

import math
from typing import Iterable

DEFAULT_AUTHOR_WEIGHT = 1.0

_NORMALIZED_MIN = 0.5
_NORMALIZED_MAX = 2.0


class AuthorScorer:
    """Compute author credibility weights per platform."""

    def score_twitter_author(self, author_metrics: dict) -> float:
        """Compute the raw Twitter credibility score for one author.

        Args:
            author_metrics: Dict containing followers_count, following_count,
                tweet_count, account_age_days, and verified.

        Returns:
            Raw author weight prior to batch normalization.
        """

        followers = max(0, int(author_metrics.get("followers_count", 0) or 0))
        following = max(0, int(author_metrics.get("following_count", 0) or 0))
        account_age_days = max(0, int(author_metrics.get("account_age_days", 0) or 0))
        verified = bool(author_metrics.get("verified", False))

        follower_score = math.log(1.0 + followers)
        age_score = min(account_age_days / 365.0, 3.0)
        ratio_penalty = min(following / max(followers, 1), 1.0)
        verified_bonus = 1.2 if verified else 1.0
        return (
            (follower_score + age_score) * (1.0 - ratio_penalty * 0.3) * verified_bonus
        )

    def score_reddit_author(self, author_metrics: dict) -> float:
        """Compute the raw Reddit credibility score for one author.

        Args:
            author_metrics: Dict containing comment_karma, post_karma, and
                account_age_days.

        Returns:
            Raw author weight prior to batch normalization.
        """

        comment_karma = max(0, int(author_metrics.get("comment_karma", 0) or 0))
        post_karma = max(0, int(author_metrics.get("post_karma", 0) or 0))
        account_age_days = max(0, int(author_metrics.get("account_age_days", 0) or 0))

        karma_score = math.log(1.0 + comment_karma + post_karma)
        age_score = min(account_age_days / 365.0, 3.0)
        return karma_score * age_score

    def normalize_batch(self, raw_weights: Iterable[float]) -> list[float]:
        """Min-max normalize raw author weights to the [0.5, 2.0] range.

        Args:
            raw_weights: Raw author weight values for the batch.

        Returns:
            List of normalized author weights, one per input value.
        """

        values = list(raw_weights)
        if not values:
            return []
        lo = min(values)
        hi = max(values)
        span = hi - lo
        if span <= 0:
            return [DEFAULT_AUTHOR_WEIGHT for _ in values]
        scale = _NORMALIZED_MAX - _NORMALIZED_MIN
        return [_NORMALIZED_MIN + ((value - lo) / span) * scale for value in values]


__all__: list[str] = ["AuthorScorer", "DEFAULT_AUTHOR_WEIGHT"]

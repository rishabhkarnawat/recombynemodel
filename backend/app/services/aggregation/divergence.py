"""Divergence detection helpers for Recombyne."""

from app.schemas.sentiment import WeightedResult


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

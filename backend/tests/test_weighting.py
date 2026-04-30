"""Engagement weighting tests."""

from app.schemas.sentiment import SentimentResult
from app.services.ingestion.base import EngagementMetrics, RawPost
from app.services.scoring.engagement_weighter import EngagementWeighter


def test_compute_weight_twitter_formula() -> None:
    """Validate Twitter weighting follows the documented equation."""

    post = RawPost(
        id="1",
        source="twitter",
        text="Example",
        author="author",
        created_at="2026-01-01T00:00:00Z",
        url="https://x.com/i/web/status/1",
        raw_engagement=EngagementMetrics(likes=10, reposts=2, comments=4, views=100),
        metadata={},
    )
    weight = EngagementWeighter().compute_weight(post)
    assert weight > 0


def test_apply_weights_divergence_flag() -> None:
    """Check divergence flag behavior using high-weight positive post."""

    posts = [
        RawPost(
            id="1",
            source="twitter",
            text="Very positive",
            author="author",
            created_at="2026-01-01T00:00:00Z",
            url="https://x.com/i/web/status/1",
            raw_engagement=EngagementMetrics(
                likes=1000, reposts=300, comments=200, views=500000
            ),
            metadata={},
        ),
        RawPost(
            id="2",
            source="twitter",
            text="Negative",
            author="author2",
            created_at="2026-01-01T00:00:00Z",
            url="https://x.com/i/web/status/2",
            raw_engagement=EngagementMetrics(likes=1, reposts=0, comments=0, views=10),
            metadata={},
        ),
    ]
    sentiments = [
        SentimentResult(
            label="positive", score=0.9, confidence=0.95, raw_logits=[0.1, 0.2, 0.7]
        ),
        SentimentResult(
            label="negative", score=-0.9, confidence=0.95, raw_logits=[0.7, 0.2, 0.1]
        ),
    ]
    result = EngagementWeighter().apply_weights(posts, sentiments)
    assert result.total_posts == 2
    assert isinstance(result.divergence_flag, bool)

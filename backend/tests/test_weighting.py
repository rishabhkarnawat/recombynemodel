"""Engagement weighting tests."""

from datetime import datetime, timedelta, timezone

from app.schemas.sentiment import SentimentResult
from app.services.aggregation.divergence import DivergenceDetector
from app.services.ingestion.base import EngagementMetrics, RawPost
from app.services.scoring.engagement_weighter import EngagementWeighter


def _make_post(
    *,
    likes: int = 0,
    reposts: int = 0,
    comments: int = 0,
    views: int | None = None,
    source: str = "twitter",
    hours_ago: int = 0,
    post_id: str = "p1",
    now: datetime | None = None,
    upvote_ratio: float | None = None,
) -> RawPost:
    """Build a synthetic RawPost for weighting tests."""

    now = now or datetime(2026, 4, 30, 12, 0, tzinfo=timezone.utc)
    return RawPost(
        id=post_id,
        source=source,
        text="weighting fixture",
        author="author",
        created_at=now - timedelta(hours=hours_ago),
        url=f"https://x.com/i/web/status/{post_id}",
        raw_engagement=EngagementMetrics(
            likes=likes,
            reposts=reposts,
            comments=comments,
            views=views,
            upvote_ratio=upvote_ratio,
        ),
        metadata={},
    )


def _sentiment(score: float, label: str = "positive") -> SentimentResult:
    return SentimentResult(
        label=label,
        score=score,
        confidence=abs(score) or 0.6,
        raw_logits=[0.0, 0.0, 0.0],
        is_english=True,
    )


def test_high_engagement_post_outweighs_low_engagement_post() -> None:
    """A high-engagement positive post should weigh more than a low-engagement one."""

    now = datetime(2026, 4, 30, 12, 0, tzinfo=timezone.utc)
    weighter = EngagementWeighter(use_author_scoring=False, now=now)

    high = _make_post(
        likes=2000, reposts=300, comments=200, views=500000, post_id="hi", now=now
    )
    low = _make_post(likes=2, reposts=0, comments=0, views=10, post_id="lo", now=now)

    assert weighter.compute_weight(high) > weighter.compute_weight(low)


def test_time_decay_reduces_weight_over_time() -> None:
    """Time decay should monotonically reduce weight as a post ages."""

    now = datetime(2026, 4, 30, 12, 0, tzinfo=timezone.utc)
    weighter = EngagementWeighter(use_author_scoring=False, now=now)

    fresh = _make_post(
        likes=100,
        reposts=20,
        comments=10,
        views=50_000,
        post_id="fresh",
        hours_ago=0,
        now=now,
    )
    one_day = _make_post(
        likes=100,
        reposts=20,
        comments=10,
        views=50_000,
        post_id="oneday",
        hours_ago=24,
        now=now,
    )
    three_days = _make_post(
        likes=100,
        reposts=20,
        comments=10,
        views=50_000,
        post_id="threedays",
        hours_ago=72,
        now=now,
    )

    assert weighter.compute_weight(fresh) > weighter.compute_weight(one_day)
    assert weighter.compute_weight(one_day) > weighter.compute_weight(three_days)


def test_log_normalization_prevents_outlier_dominance() -> None:
    """Log normalization should keep a viral post from dominating the average."""

    now = datetime(2026, 4, 30, 12, 0, tzinfo=timezone.utc)
    weighter = EngagementWeighter(use_author_scoring=False, now=now)

    posts = [_make_post(likes=10, post_id=f"low-{i}", now=now) for i in range(20)]
    posts.append(_make_post(likes=5_000_000, post_id="viral", now=now))
    sentiments = [_sentiment(0.5, "positive") for _ in range(20)]
    sentiments.append(_sentiment(-0.95, "negative"))

    result = weighter.apply_weights(posts, sentiments)
    assert result.weighted_score > -0.6


def test_divergence_flag_detects_weighted_positive_skew() -> None:
    """Divergence flag should fire when weighted exceeds raw by >0.15."""

    now = datetime(2026, 4, 30, 12, 0, tzinfo=timezone.utc)
    weighter = EngagementWeighter(use_author_scoring=False, now=now)

    posts = [
        _make_post(
            likes=10_000,
            reposts=2_000,
            comments=1_500,
            views=2_000_000,
            post_id="loud",
            now=now,
        ),
        _make_post(likes=2, post_id="quiet1", now=now),
        _make_post(likes=2, post_id="quiet2", now=now),
    ]
    sentiments = [
        _sentiment(0.95, "positive"),
        _sentiment(-0.6, "negative"),
        _sentiment(-0.6, "negative"),
    ]
    result = weighter.apply_weights(posts, sentiments)
    assert result.divergence_flag is True
    assert result.divergence_direction == "weighted_positive"


def test_top_signals_returns_five_sorted_descending() -> None:
    """top_signals must return at most 5 entries sorted by signal_strength."""

    now = datetime(2026, 4, 30, 12, 0, tzinfo=timezone.utc)
    posts = [
        _make_post(likes=(i + 1) * 100, post_id=f"p{i}", now=now) for i in range(8)
    ]
    sentiments = [_sentiment(0.6, "positive") for _ in range(8)]
    result = EngagementWeighter(use_author_scoring=False, now=now).apply_weights(
        posts, sentiments
    )
    assert len(result.top_signals) == 5
    strengths = [signal.signal_strength for signal in result.top_signals]
    assert strengths == sorted(strengths, reverse=True)


def test_platform_divergence_flag_when_sources_disagree() -> None:
    """DivergenceDetector should flag platform divergence when scores diverge."""

    now = datetime(2026, 4, 30, 12, 0, tzinfo=timezone.utc)
    posts = [
        _make_post(source="twitter", likes=200, post_id="t1", now=now),
        _make_post(source="twitter", likes=200, post_id="t2", now=now),
        _make_post(source="reddit", likes=200, post_id="r1", now=now),
        _make_post(source="reddit", likes=200, post_id="r2", now=now),
    ]
    sentiments = [
        _sentiment(0.85, "positive"),
        _sentiment(0.85, "positive"),
        _sentiment(-0.7, "negative"),
        _sentiment(-0.7, "negative"),
    ]
    weighted = EngagementWeighter(use_author_scoring=False, now=now).apply_weights(
        posts, sentiments
    )
    flags = DivergenceDetector().build_structured_flags(weighted, posts, sentiments)
    assert any(flag.type == "platform" for flag in flags)

"""Ingestion mapping and credential validation tests."""

from datetime import datetime, timezone

import pytest

from app.services.ingestion.base import EngagementMetrics, RawPost
from app.services.ingestion.post_filter import PostFilter
from app.services.ingestion.reddit import RedditIngester
from app.services.ingestion.twitter import TwitterIngester
from app.utils.errors import RecombynKeyError


def test_engagement_metrics_are_non_negative(sample_raw_posts) -> None:
    """EngagementMetrics fields cannot be negative."""

    for post in sample_raw_posts:
        assert post.raw_engagement.likes >= 0
        assert post.raw_engagement.reposts >= 0
        assert post.raw_engagement.comments >= 0
        if post.raw_engagement.views is not None:
            assert post.raw_engagement.views >= 0


def test_validate_credentials_returns_false_without_env(monkeypatch) -> None:
    """validate_credentials should be False when env vars are missing."""

    monkeypatch.setattr("app.config.settings.twitter_bearer_token", None)
    monkeypatch.setattr("app.config.settings.reddit_client_id", None)
    monkeypatch.setattr("app.config.settings.reddit_client_secret", None)

    assert TwitterIngester().validate_credentials() is False
    assert RedditIngester().validate_credentials() is False


def test_twitter_fetch_raises_when_credentials_missing(monkeypatch) -> None:
    """TwitterIngester must raise a typed key error when token is absent."""

    monkeypatch.setattr("app.config.settings.twitter_bearer_token", None)
    ingester = TwitterIngester()
    import asyncio

    with pytest.raises(RecombynKeyError):
        asyncio.run(ingester.fetch("anything", 24, 10))


def test_post_filter_rejects_short_and_duplicate_posts() -> None:
    """PostFilter must reject too-short posts and duplicates."""

    now = datetime(2026, 4, 30, 12, 0, tzinfo=timezone.utc)
    posts = [
        RawPost(
            id="short",
            source="twitter",
            text="hi",
            author="u",
            created_at=now,
            url="https://x.com/i/web/status/short",
            raw_engagement=EngagementMetrics(),
            metadata={},
        ),
        RawPost(
            id="dup1",
            source="twitter",
            text="Recombyne is shipping nicely today.",
            author="u",
            created_at=now,
            url="https://x.com/i/web/status/dup1",
            raw_engagement=EngagementMetrics(),
            metadata={},
        ),
        RawPost(
            id="dup2",
            source="twitter",
            text="Recombyne is shipping nicely today.",
            author="u2",
            created_at=now,
            url="https://x.com/i/web/status/dup2",
            raw_engagement=EngagementMetrics(),
            metadata={},
        ),
    ]
    result = PostFilter().filter(posts)
    reasons = [item.reason for item in result.rejected]
    assert "too_short" in reasons
    assert "duplicate" in reasons

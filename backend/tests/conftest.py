"""Shared pytest fixtures for backend tests."""

from datetime import datetime, timezone

import pytest
from app.services.ingestion.base import EngagementMetrics, RawPost


@pytest.fixture
def sample_twitter_post() -> RawPost:
    """Return a sample Twitter RawPost for unit tests."""

    return RawPost(
        id="tw-1",
        source="twitter",
        text="Recombyne looks promising.",
        author="user1",
        created_at=datetime.now(timezone.utc),
        url="https://x.com/i/web/status/1",
        raw_engagement=EngagementMetrics(
            likes=100, reposts=20, comments=10, views=10000
        ),
        metadata={},
    )

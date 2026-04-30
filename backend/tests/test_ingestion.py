"""Ingestion layer tests."""

from app.services.ingestion.reddit import RedditIngester
from app.services.ingestion.twitter import TwitterIngester


def test_twitter_validate_credentials_shape() -> None:
    """Ensure Twitter validator returns a boolean for config readiness."""

    assert isinstance(TwitterIngester().validate_credentials(), bool)


def test_reddit_validate_credentials_shape() -> None:
    """Ensure Reddit validator returns a boolean for config readiness."""

    assert isinstance(RedditIngester().validate_credentials(), bool)

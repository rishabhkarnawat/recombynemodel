"""Twitter/X ingestion service using Tweepy."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

import tweepy
from app.config import settings
from app.services.ingestion.base import (BaseIngester, EngagementMetrics,
                                         RawPost, RecombyneFetchError)

logger = logging.getLogger(__name__)


class TwitterIngester(BaseIngester):
    """Ingest posts from Twitter/X recent search endpoint."""

    def __init__(self) -> None:
        """Initialize Twitter API client if token is available."""

        self._token = settings.twitter_bearer_token
        self._client = (
            tweepy.Client(bearer_token=self._token, wait_on_rate_limit=False)
            if self._token
            else None
        )

    def _ensure_client(self) -> tweepy.Client:
        """Return API client or raise a clear credential error."""

        if self._client is None:
            raise RecombyneFetchError(
                "Twitter credentials are missing. Set TWITTER_BEARER_TOKEN in .env."
            )
        return self._client

    async def fetch(self, query: str, window_hours: int, limit: int) -> list[RawPost]:
        """Fetch tweets from Twitter v2 recent search with backoff."""

        client = self._ensure_client()
        start_time = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        attempts = 0
        wait_seconds = 1.0
        while attempts < 5:
            attempts += 1
            try:
                response = await asyncio.to_thread(
                    client.search_recent_tweets,
                    query=query,
                    tweet_fields=[
                        "public_metrics",
                        "author_id",
                        "created_at",
                        "entities",
                    ],
                    start_time=start_time,
                    max_results=min(100, max(10, limit)),
                )
                logger.info("Twitter rate headers: %s", getattr(response, "meta", {}))
                tweets = response.data or []
                normalized: list[RawPost] = []
                for tweet in tweets[:limit]:
                    metrics = tweet.public_metrics or {}
                    normalized.append(
                        RawPost(
                            id=str(tweet.id),
                            source="twitter",
                            text=tweet.text,
                            author=str(tweet.author_id),
                            created_at=tweet.created_at,
                            url=f"https://x.com/i/web/status/{tweet.id}",
                            raw_engagement=EngagementMetrics(
                                likes=int(metrics.get("like_count", 0)),
                                reposts=int(metrics.get("retweet_count", 0)),
                                comments=int(metrics.get("reply_count", 0)),
                                views=(
                                    int(metrics.get("impression_count", 0))
                                    if metrics.get("impression_count")
                                    else None
                                ),
                                upvote_ratio=None,
                            ),
                            metadata={"entities": getattr(tweet, "entities", None)},
                        )
                    )
                return normalized
            except tweepy.Unauthorized as exc:
                raise RecombyneFetchError(
                    "Twitter credentials are invalid or expired."
                ) from exc
            except tweepy.TooManyRequests:
                logger.warning(
                    "Twitter rate limit hit. retry=%s sleep=%s", attempts, wait_seconds
                )
                await asyncio.sleep(wait_seconds)
                wait_seconds *= 2
            except Exception as exc:
                raise RecombyneFetchError(f"Twitter fetch failed: {exc}") from exc
        raise RecombyneFetchError("Twitter rate limit exceeded after retries.")

    async def stream(self, query: str, callback) -> None:
        """Stream tweets for a query."""

        posts = await self.fetch(query=query, window_hours=1, limit=25)
        for post in posts:
            maybe = callback(post)
            if asyncio.iscoroutine(maybe):
                await maybe

    def validate_credentials(self) -> bool:
        """Check whether environment token exists."""

        return bool(self._token)

    def validate_credentials_with_override(self, token: str | None) -> tuple[bool, str]:
        """Validate provided token format."""

        if not token and not self._token:
            return (False, "Missing TWITTER_BEARER_TOKEN.")
        if token and len(token.strip()) < 20:
            return (False, "Token appears malformed or too short.")
        return (True, "Twitter bearer token format looks valid.")

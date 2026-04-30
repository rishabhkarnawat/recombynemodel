"""Twitter/X ingestion service using Tweepy."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

import tweepy

from app.config import settings
from app.services.ingestion.base import (
    AuthorMetrics,
    BaseIngester,
    EngagementMetrics,
    RawPost,
)
from app.utils.errors import (
    RecombyneFetchError,
    RecombynKeyError,
    RecombynRateLimitError,
)

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
            raise RecombynKeyError(
                "Twitter credentials are missing. Set TWITTER_BEARER_TOKEN in .env.",
                code="TWITTER_KEY_MISSING",
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
                        "lang",
                    ],
                    expansions=["author_id"],
                    user_fields=[
                        "public_metrics",
                        "verified",
                        "created_at",
                    ],
                    start_time=start_time,
                    max_results=min(100, max(10, limit)),
                )
                logger.info("Twitter rate headers: %s", getattr(response, "meta", {}))
                tweets = response.data or []
                user_lookup: dict[str, AuthorMetrics] = {}
                includes = getattr(response, "includes", None) or {}
                for user in includes.get("users", []) or []:
                    user_metrics = getattr(user, "public_metrics", None) or {}
                    created_at = getattr(user, "created_at", None)
                    age_days = None
                    if created_at is not None:
                        age_days = max(
                            0,
                            int((datetime.now(timezone.utc) - created_at).days),
                        )
                    user_lookup[str(user.id)] = AuthorMetrics(
                        followers_count=int(
                            user_metrics.get("followers_count", 0) or 0
                        ),
                        following_count=int(
                            user_metrics.get("following_count", 0) or 0
                        ),
                        tweet_count=int(user_metrics.get("tweet_count", 0) or 0),
                        account_age_days=age_days,
                        verified=bool(getattr(user, "verified", False) or False),
                    )

                normalized: list[RawPost] = []
                for tweet in tweets[:limit]:
                    metrics = tweet.public_metrics or {}
                    author_metrics = user_lookup.get(
                        str(getattr(tweet, "author_id", ""))
                    )
                    lang = getattr(tweet, "lang", None)
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
                            author_metrics=author_metrics,
                            is_english=(lang == "en") if lang else None,
                            metadata={
                                "entities": getattr(tweet, "entities", None),
                                "lang": lang,
                            },
                        )
                    )
                return normalized
            except tweepy.Unauthorized as exc:
                raise RecombynKeyError(
                    "Twitter credentials are invalid or expired.",
                    code="TWITTER_AUTH_FAILED",
                ) from exc
            except tweepy.TooManyRequests as exc:
                logger.warning(
                    "Twitter rate limit hit. retry=%s sleep=%s", attempts, wait_seconds
                )
                if attempts >= 5:
                    raise RecombynRateLimitError(
                        "Twitter rate limit exceeded after retries.",
                        retry_after=int(wait_seconds),
                        code="TWITTER_RATE_LIMIT",
                    ) from exc
                await asyncio.sleep(wait_seconds)
                wait_seconds *= 2
            except Exception as exc:
                raise RecombyneFetchError(
                    f"Twitter fetch failed: {exc}",
                    code="TWITTER_FETCH_FAILED",
                ) from exc
        raise RecombynRateLimitError(
            "Twitter rate limit exceeded after retries.",
            retry_after=int(wait_seconds),
            code="TWITTER_RATE_LIMIT",
        )

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

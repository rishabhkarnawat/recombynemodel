"""Reddit ingestion service using PRAW."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import praw
from app.config import settings
from app.services.ingestion.base import (
    AuthorMetrics,
    BaseIngester,
    EngagementMetrics,
    RawPost,
)
from app.utils.errors import RecombyneFetchError, RecombynKeyError
from prawcore import PrawcoreException


class RedditIngester(BaseIngester):
    """Ingest Reddit submissions across configured subreddits."""

    def __init__(self, subreddits: str = "all") -> None:
        """Configure Reddit client and source scope."""

        self._subreddits = subreddits
        self._client_id = settings.reddit_client_id
        self._client_secret = settings.reddit_client_secret
        self._user_agent = settings.reddit_user_agent
        self._client = (
            praw.Reddit(
                client_id=self._client_id,
                client_secret=self._client_secret,
                user_agent=self._user_agent,
                check_for_async=False,
            )
            if self._client_id and self._client_secret
            else None
        )

    def _ensure_client(self) -> praw.Reddit:
        """Return configured Reddit client or raise."""

        if self._client is None:
            raise RecombynKeyError(
                "Reddit credentials are missing. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env.",
                code="REDDIT_KEY_MISSING",
            )
        return self._client

    @staticmethod
    def _build_author_metrics(submission) -> AuthorMetrics | None:
        """Best-effort author metrics extraction without extra API calls."""

        author = getattr(submission, "author", None)
        if author is None:
            return None
        try:
            comment_karma = int(getattr(author, "comment_karma", 0) or 0)
            post_karma = int(getattr(author, "link_karma", 0) or 0)
            created_utc = getattr(author, "created_utc", None)
            age_days = None
            if created_utc:
                created = datetime.fromtimestamp(float(created_utc), tz=timezone.utc)
                age_days = max(0, int((datetime.now(timezone.utc) - created).days))
            return AuthorMetrics(
                comment_karma=comment_karma,
                post_karma=post_karma,
                account_age_days=age_days,
            )
        except Exception:
            return None

    async def fetch(self, query: str, window_hours: int, limit: int) -> list[RawPost]:
        """Fetch Reddit submissions and normalize output."""

        client = self._ensure_client()
        cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        try:
            subreddit = client.subreddit(self._subreddits)
            submissions = await asyncio.to_thread(
                lambda: list(subreddit.search(query=query, limit=limit, sort="new"))
            )
        except PrawcoreException as exc:
            raise RecombyneFetchError(
                f"Reddit API request failed: {exc}",
                code="REDDIT_FETCH_FAILED",
            ) from exc
        except Exception as exc:
            raise RecombyneFetchError(
                f"Reddit fetch failed: {exc}",
                code="REDDIT_FETCH_FAILED",
            ) from exc

        posts: list[RawPost] = []
        for submission in submissions:
            created = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
            if created < cutoff:
                continue
            posts.append(
                RawPost(
                    id=submission.id,
                    source="reddit",
                    text=f"{submission.title}\n\n{submission.selftext or ''}".strip(),
                    author=str(submission.author) if submission.author else "[deleted]",
                    created_at=created,
                    url=f"https://reddit.com{submission.permalink}",
                    raw_engagement=EngagementMetrics(
                        likes=int(submission.score),
                        reposts=int(getattr(submission, "num_crossposts", 0)),
                        comments=int(submission.num_comments),
                        views=None,
                        upvote_ratio=(
                            float(submission.upvote_ratio)
                            if submission.upvote_ratio is not None
                            else None
                        ),
                    ),
                    author_metrics=self._build_author_metrics(submission),
                    is_english=None,
                    metadata={"subreddit": str(submission.subreddit)},
                )
            )
        return posts

    async def stream(self, query: str, callback) -> None:
        """Stream Reddit posts for quick incremental processing."""

        posts = await self.fetch(query=query, window_hours=1, limit=25)
        for post in posts:
            maybe = callback(post)
            if asyncio.iscoroutine(maybe):
                await maybe

    def validate_credentials(self) -> bool:
        """Check whether Reddit credentials are configured."""

        return bool(self._client_id and self._client_secret)

    def validate_credentials_with_override(
        self, client_id: str | None, client_secret: str | None, user_agent: str | None
    ) -> tuple[bool, str]:
        """Validate provided credential override payload."""

        candidate_id = client_id or self._client_id
        candidate_secret = client_secret or self._client_secret
        candidate_ua = user_agent or self._user_agent
        if not candidate_id or not candidate_secret:
            return (False, "Missing REDDIT_CLIENT_ID or REDDIT_CLIENT_SECRET.")
        if not candidate_ua:
            return (False, "Missing REDDIT_USER_AGENT.")
        return (True, "Reddit credential format looks valid.")

"""Shared pytest fixtures for backend tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.schemas.sentiment import SentimentResult
from app.services.ingestion.base import AuthorMetrics, EngagementMetrics, RawPost


@pytest.fixture
def now() -> datetime:
    """Return a stable reference timestamp for deterministic tests."""

    return datetime(2026, 4, 30, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def mock_twitter_response(now: datetime) -> list[dict]:
    """Return realistic-shaped Twitter search payload for tests."""

    base = []
    for index in range(10):
        likes = (index + 1) * 25
        reposts = (index + 1) * 5
        comments = (index + 1) * 3
        views = (index + 1) * 4500
        base.append(
            {
                "id": f"tw-{index}",
                "text": f"Sample tweet number {index} about Recombyne.",
                "author_id": f"user-{index}",
                "created_at": (now - timedelta(hours=index)).isoformat(),
                "public_metrics": {
                    "like_count": likes,
                    "retweet_count": reposts,
                    "reply_count": comments,
                    "impression_count": views,
                },
                "lang": "en",
            }
        )
    base.append(
        {
            "id": "tw-viral",
            "text": "VIRAL: Recombyne dashboard just shipped, this is huge!",
            "author_id": "user-viral",
            "created_at": now.isoformat(),
            "public_metrics": {
                "like_count": 50000,
                "retweet_count": 12000,
                "reply_count": 3000,
                "impression_count": 5000000,
            },
            "lang": "en",
        }
    )
    return base


@pytest.fixture
def mock_reddit_response(now: datetime) -> list[dict]:
    """Return realistic-shaped Reddit submission payload for tests."""

    submissions = []
    for index in range(10):
        submissions.append(
            {
                "id": f"rd-{index}",
                "title": f"Reddit thread {index} discussing Recombyne",
                "selftext": "Some commentary on Recombyne weighting behavior.",
                "score": (index + 1) * 30,
                "num_comments": (index + 1) * 8,
                "num_crossposts": index,
                "upvote_ratio": min(0.99, 0.6 + index * 0.04),
                "created_utc": (now - timedelta(hours=index * 2)).timestamp(),
                "author": f"redditor-{index}",
                "subreddit": "test",
                "permalink": f"/r/test/comments/rd{index}",
            }
        )
    return submissions


@pytest.fixture
def sample_raw_posts(
    mock_twitter_response: list[dict], mock_reddit_response: list[dict], now: datetime
) -> list[RawPost]:
    """Return mixed Twitter + Reddit RawPost objects from mock payloads."""

    posts: list[RawPost] = []
    for tweet in mock_twitter_response[:10]:
        metrics = tweet["public_metrics"]
        posts.append(
            RawPost(
                id=str(tweet["id"]),
                source="twitter",
                text=tweet["text"],
                author=tweet["author_id"],
                created_at=datetime.fromisoformat(tweet["created_at"]),
                url=f"https://x.com/i/web/status/{tweet['id']}",
                raw_engagement=EngagementMetrics(
                    likes=metrics["like_count"],
                    reposts=metrics["retweet_count"],
                    comments=metrics["reply_count"],
                    views=metrics["impression_count"],
                ),
                author_metrics=AuthorMetrics(
                    followers_count=2000,
                    following_count=400,
                    tweet_count=1500,
                    account_age_days=900,
                    verified=False,
                ),
                is_english=True,
                metadata={"lang": tweet["lang"]},
            )
        )
    for submission in mock_reddit_response[:10]:
        posts.append(
            RawPost(
                id=submission["id"],
                source="reddit",
                text=f"{submission['title']}\n\n{submission['selftext']}".strip(),
                author=submission["author"],
                created_at=datetime.fromtimestamp(
                    submission["created_utc"], tz=timezone.utc
                ),
                url=f"https://reddit.com{submission['permalink']}",
                raw_engagement=EngagementMetrics(
                    likes=submission["score"],
                    reposts=submission["num_crossposts"],
                    comments=submission["num_comments"],
                    views=None,
                    upvote_ratio=submission["upvote_ratio"],
                ),
                author_metrics=AuthorMetrics(
                    comment_karma=2000,
                    post_karma=500,
                    account_age_days=1200,
                ),
                is_english=True,
                metadata={"subreddit": submission["subreddit"]},
            )
        )
    return posts


@pytest.fixture
def sample_sentiments(sample_raw_posts: list[RawPost]) -> list[SentimentResult]:
    """Return deterministic sentiment results aligned with sample_raw_posts."""

    results: list[SentimentResult] = []
    for index, post in enumerate(sample_raw_posts):
        if index % 2 == 0:
            score = 0.85
            label = "positive"
            logits = [0.05, 0.10, 0.85]
        else:
            score = -0.65
            label = "negative"
            logits = [0.65, 0.20, 0.15]
        if "VIRAL" in post.text:
            score = 0.95
            label = "positive"
            logits = [0.02, 0.03, 0.95]
        results.append(
            SentimentResult(
                label=label,
                score=score,
                confidence=abs(score),
                raw_logits=logits,
                negation_detected=False,
                sarcasm_risk=0.0,
                is_english=True,
            )
        )
    return results


@pytest.fixture
def scorer():
    """Return a RoBERTaSentimentScorer that won't load the local model."""

    from app.services.scoring.roberta import RoBERTaSentimentScorer

    instance = RoBERTaSentimentScorer()
    instance.__class__._model = None
    instance.__class__._tokenizer = None
    return instance

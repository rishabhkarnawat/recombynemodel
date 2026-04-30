"""Seed Recombyne with realistic mock query results for local exploration.

Run this script after starting the backend to populate the in-memory history
store with five themed example topics. Contributors can use this to explore
the dashboard, watchlist, and CLI without configuring real API keys.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.post import QueryResponse
from app.schemas.sentiment import (
    DivergenceFlag,
    SentimentResult,
    TimelineBucket,
    TopSignal,
    WeightedResult,
)
from app.services.aggregation.divergence import DivergenceDetector
from app.services.ingestion.base import EngagementMetrics, RawPost
from app.services.scoring.engagement_weighter import EngagementWeighter
from app.utils.store import history_store

from scripts.generate_mock_posts import generate_posts

TOPICS = [
    "Waymo",
    "Arc Browser",
    "Kalshi",
    "New Balance 1906R",
    "Polymarket",
]


def _post_from_mock(payload: dict) -> RawPost:
    """Convert a mock JSON payload into a RawPost."""

    engagement = payload["raw_engagement"]
    return RawPost(
        id=payload["id"],
        source=payload["source"],
        text=payload["text"],
        author=payload["author"],
        created_at=datetime.fromisoformat(payload["created_at"]),
        url=payload["url"],
        raw_engagement=EngagementMetrics(
            likes=engagement["likes"],
            reposts=engagement["reposts"],
            comments=engagement["comments"],
            views=engagement.get("views"),
            upvote_ratio=engagement.get("upvote_ratio"),
        ),
        is_english=payload.get("is_english", True),
        metadata=payload.get("metadata", {}),
    )


def _scripted_sentiment(post: RawPost) -> SentimentResult:
    """Deterministic sentiment derived from the mock mood metadata."""

    mood = (post.metadata or {}).get("mood", "neutral")
    if mood == "positive":
        return SentimentResult(
            label="positive",
            score=0.8,
            confidence=0.85,
            raw_logits=[0.05, 0.10, 0.85],
            is_english=True,
        )
    if mood == "negative":
        return SentimentResult(
            label="negative",
            score=-0.7,
            confidence=0.78,
            raw_logits=[0.78, 0.15, 0.07],
            is_english=True,
        )
    return SentimentResult(
        label="neutral",
        score=0.0,
        confidence=0.55,
        raw_logits=[0.30, 0.55, 0.15],
        is_english=True,
    )


def _build_query_response(topic: str) -> QueryResponse:
    """Build a fully-populated QueryResponse for a topic seed."""

    twitter_posts = [
        _post_from_mock(p) for p in generate_posts(topic, 12, "twitter", 168)
    ]
    reddit_posts = [_post_from_mock(p) for p in generate_posts(topic, 8, "reddit", 168)]
    posts = twitter_posts + reddit_posts
    sentiments = [_scripted_sentiment(post) for post in posts]
    weighted = EngagementWeighter().apply_weights(posts, sentiments)
    structured = DivergenceDetector().build_structured_flags(
        weighted, posts, sentiments
    )
    return QueryResponse(
        query_id=str(uuid4()),
        topic=topic,
        sources=["twitter", "reddit"],
        window_hours=168,
        weighted_result=weighted,
        timeline=[
            TimelineBucket(
                timestamp=posts[0].created_at,
                raw_score=weighted.raw_score,
                weighted_score=weighted.weighted_score,
                post_count=weighted.total_posts,
                dominant_label=(
                    "positive" if weighted.weighted_score >= 0 else "negative"
                ),
            )
        ],
        divergence_flags=[flag.explanation for flag in structured],
        structured_divergence_flags=structured,
        co_mentions=[],
        runtime_ms=42.0,
        queried_at=datetime.now(timezone.utc),
    )


async def main() -> None:
    """Populate the history store with deterministic seed queries."""

    for topic in TOPICS:
        response = _build_query_response(topic)
        history_store.add(response)
        weighted: WeightedResult = response.weighted_result
        print(
            f"Seeded {topic}: weighted={weighted.weighted_score:+.3f}, "
            f"raw={weighted.raw_score:+.3f}, posts={weighted.total_posts}"
        )

    # Suppress unused-import warnings from optional surfaces.
    _ = (DivergenceFlag, TopSignal)


if __name__ == "__main__":
    asyncio.run(main())

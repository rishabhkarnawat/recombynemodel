"""Watchlist routes and background refresh trigger."""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.schemas.post import (
    QueryRequest,
    WatchlistEntry,
    WatchlistEntryRequest,
    WatchlistResponse,
)
from app.services.aggregation.divergence import DivergenceDetector
from app.services.aggregation.timeline import TimelineAggregator
from app.services.ingestion.post_filter import PostFilter
from app.services.ingestion.reddit import RedditIngester
from app.services.ingestion.twitter import TwitterIngester
from app.services.scoring.engagement_weighter import EngagementWeighter
from app.services.scoring.entity_extractor import EntityExtractor
from app.services.scoring.roberta import RoBERTaSentimentScorer
from app.utils.store import history_store, watchlist_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/watchlist", tags=["Watchlist"])


@router.get(
    "",
    response_model=WatchlistResponse,
    summary="List tracked watchlist topics",
)
async def list_watchlist() -> WatchlistResponse:
    """Return all tracked topics with their last refresh state."""

    return WatchlistResponse(entries=watchlist_store.list())


@router.post(
    "",
    response_model=WatchlistEntry,
    summary="Add a topic to the watchlist",
)
async def add_watchlist(payload: WatchlistEntryRequest) -> WatchlistEntry:
    """Insert a new topic into the local watchlist."""

    return watchlist_store.add(
        topic=payload.topic,
        sources=list(payload.sources),
        window_hours=payload.window_hours,
        refresh_interval_minutes=payload.refresh_interval_minutes,
    )


@router.delete(
    "/{entry_id}",
    summary="Remove a watchlist topic",
)
async def remove_watchlist(entry_id: str) -> dict[str, bool]:
    """Remove a watchlist entry by ID."""

    removed = watchlist_store.remove(entry_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Watchlist entry not found")
    return {"removed": True}


async def _refresh_entry(entry: WatchlistEntry) -> None:
    """Re-run a query for a watchlist entry and persist the new result."""

    try:
        ingesters = []
        if "twitter" in entry.sources:
            ingesters.append(TwitterIngester())
        if "reddit" in entry.sources:
            ingesters.append(RedditIngester())

        posts = []
        for ingester in ingesters:
            posts.extend(await ingester.fetch(entry.topic, entry.window_hours, 200))

        filtered = PostFilter().filter(posts)
        posts = filtered.passed

        scorer = RoBERTaSentimentScorer()
        sentiments = await scorer.batch_score([post.text for post in posts])
        weighted = EngagementWeighter().apply_weights(posts, sentiments)
        timeline = TimelineAggregator().build_timeline(posts, sentiments).buckets
        structured_flags = DivergenceDetector().build_structured_flags(
            weighted, posts, sentiments
        )
        co_mentions = EntityExtractor().extract(posts, sentiments, entry.topic)

        from datetime import datetime, timezone
        from uuid import uuid4

        from app.schemas.post import QueryResponse

        response = QueryResponse(
            query_id=str(uuid4()),
            topic=entry.topic,
            sources=list(entry.sources),
            window_hours=entry.window_hours,
            weighted_result=weighted,
            timeline=timeline,
            divergence_flags=[flag.explanation for flag in structured_flags],
            structured_divergence_flags=structured_flags,
            co_mentions=co_mentions,
            runtime_ms=0.0,
            queried_at=datetime.now(timezone.utc),
        )
        history_store.add(response)
        watchlist_store.update_after_refresh(entry.id, weighted.weighted_score)
    except Exception as exc:  # pragma: no cover - background task best effort
        logger.warning("Watchlist refresh failed for %s: %s", entry.topic, exc)


@router.post(
    "/refresh",
    summary="Trigger a watchlist refresh sweep",
)
async def trigger_refresh(background_tasks: BackgroundTasks) -> dict[str, int]:
    """Schedule background refreshes for any watchlist entries that are due."""

    due = list(watchlist_store.due_for_refresh())
    for entry in due:
        background_tasks.add_task(_refresh_entry, entry)
    return {"scheduled": len(due)}


# Re-exported helper retained so other modules don't need to import QueryRequest
__all__: list[str] = ["router", "QueryRequest"]

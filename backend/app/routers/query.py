"""Routes for executing and retrieving query analyses."""

from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4

from fastapi import APIRouter, Body, HTTPException

from app.schemas.post import (
    CachedQueryResponse,
    HistoryResponse,
    QueryRequest,
    QueryResponse,
)
from app.schemas.sentiment import SentimentResult
from app.services.aggregation.divergence import DivergenceDetector
from app.services.aggregation.timeline import TimelineAggregator
from app.services.ingestion.base import RawPost
from app.services.ingestion.post_filter import PostFilter
from app.services.ingestion.reddit import RedditIngester
from app.services.ingestion.twitter import TwitterIngester
from app.services.scoring.engagement_weighter import EngagementWeighter
from app.services.scoring.entity_extractor import EntityExtractor
from app.services.scoring.roberta import RoBERTaSentimentScorer
from app.utils.cache import query_cache
from app.utils.errors import RecombyneScoringError
from app.utils.store import history_store

router = APIRouter(
    prefix="/api/query",
    tags=["Query"],
)


async def _gather_posts(payload: QueryRequest) -> list[RawPost]:
    """Fan out ingestion across the requested sources."""

    ingesters = []
    if "twitter" in payload.sources:
        ingesters.append(TwitterIngester())
    if "reddit" in payload.sources:
        ingesters.append(RedditIngester())

    posts: list[RawPost] = []
    for ingester in ingesters:
        posts.extend(
            await ingester.fetch(payload.topic, payload.window_hours, payload.limit)
        )
    return posts


@router.post(
    "",
    response_model=QueryResponse,
    summary="Run a sentiment intelligence query",
    description=(
        "Execute the full Recombyne pipeline: ingest, filter, score, weight, "
        "build a timeline, detect divergence, and surface engagement-weighted "
        "results."
    ),
)
async def run_query(
    payload: QueryRequest = Body(
        ...,
        examples={
            "default": {
                "summary": "Track NVDA across both sources for the last 7 days",
                "value": {
                    "topic": "NVDA",
                    "sources": ["twitter", "reddit"],
                    "window_hours": 168,
                    "limit": 500,
                },
            }
        },
    ),
) -> QueryResponse:
    """Execute an end-to-end query workflow."""

    started = perf_counter()
    posts = await _gather_posts(payload)

    filtered = PostFilter().filter(posts)
    posts = filtered.passed

    scorer = RoBERTaSentimentScorer()
    try:
        sentiments: list[SentimentResult] = await scorer.batch_score(
            [post.text for post in posts]
        )
    except Exception as exc:
        raise RecombyneScoringError(
            "Failed to score posts with the sentiment engine.",
            code="SCORING_FAILED",
            context={"reason": str(exc)},
        ) from exc

    for post, sentiment in zip(posts, sentiments, strict=False):
        post.is_english = sentiment.is_english

    weighter = EngagementWeighter()
    weighted = weighter.apply_weights(posts, sentiments)

    timeline_service = TimelineAggregator()
    timeline_result = timeline_service.build_timeline(posts, sentiments, bucket="hour")

    divergence_detector = DivergenceDetector()
    structured_flags = divergence_detector.build_structured_flags(
        weighted, posts, sentiments
    )
    divergence_flags = [flag.explanation for flag in structured_flags]

    entity_extractor = EntityExtractor()
    co_mentions = entity_extractor.extract(posts, sentiments, payload.topic)

    result = QueryResponse(
        query_id=str(uuid4()),
        topic=payload.topic,
        sources=[source for source in payload.sources],
        window_hours=payload.window_hours,
        weighted_result=weighted,
        timeline=timeline_result.buckets,
        divergence_flags=divergence_flags,
        structured_divergence_flags=structured_flags,
        co_mentions=co_mentions,
        runtime_ms=round((perf_counter() - started) * 1000.0, 2),
        queried_at=datetime.now(timezone.utc),
    )
    query_cache.set(result.query_id, result)
    history_store.add(result)
    return result


@router.get(
    "/history",
    response_model=HistoryResponse,
    summary="List recent queries",
    description="Return the most recent queries executed by the local instance.",
)
async def get_history(limit: int = 20) -> HistoryResponse:
    """Return the recent history of executed queries."""

    return HistoryResponse(entries=history_store.list(limit=limit))


@router.get(
    "/{query_id}",
    response_model=CachedQueryResponse,
    summary="Fetch a previously executed query",
)
async def get_cached_query(query_id: str) -> CachedQueryResponse:
    """Return a cached query result by ID."""

    query = query_cache.get(query_id) or history_store.get(query_id)
    if query is None:
        return CachedQueryResponse(found=False, query=None)
    return CachedQueryResponse(found=True, query=query)


@router.get(
    "/{query_id}/export",
    summary="Export a stored query result",
    description="Export a query result as CSV (one row per post) or JSON.",
)
async def export_query(query_id: str, format: str = "json"):
    """Export a query result in the requested format."""

    response = query_cache.get(query_id) or history_store.get(query_id)
    if response is None:
        raise HTTPException(status_code=404, detail="Query not found")

    if format.lower() == "json":
        return response.model_dump()

    if format.lower() == "csv":
        from io import StringIO

        from fastapi.responses import Response

        buffer = StringIO()
        buffer.write(
            "source,text,author,created_at,likes,reposts,comments,views,raw_sentiment,sentiment_label,confidence,weight,signal_strength\n"
        )
        for signal in response.weighted_result.top_signals:
            buffer.write(
                ",".join(
                    [
                        signal.post.source,
                        '"' + signal.post.text.replace('"', "'") + '"',
                        signal.post.author,
                        signal.post.created_at.isoformat(),
                        str(signal.post.raw_engagement.likes),
                        str(signal.post.raw_engagement.reposts),
                        str(signal.post.raw_engagement.comments),
                        str(signal.post.raw_engagement.views or ""),
                        f"{signal.sentiment.score:.6f}",
                        signal.sentiment.label,
                        f"{signal.sentiment.confidence:.6f}",
                        f"{signal.weight:.6f}",
                        f"{signal.signal_strength:.6f}",
                    ]
                )
                + "\n"
            )
        return Response(
            content=buffer.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=recombyne-{query_id}.csv"
            },
        )

    raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

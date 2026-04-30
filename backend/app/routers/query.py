"""Routes for executing and retrieving query analyses."""

from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4

from app.schemas.post import CachedQueryResponse, QueryRequest, QueryResponse
from app.services.aggregation.divergence import DivergenceDetector
from app.services.aggregation.timeline import TimelineAggregator
from app.services.ingestion.reddit import RedditIngester
from app.services.ingestion.twitter import TwitterIngester
from app.services.scoring.engagement_weighter import EngagementWeighter
from app.services.scoring.roberta import RoBERTaSentimentScorer
from app.utils.cache import query_cache
from fastapi import APIRouter

router = APIRouter(prefix="/api/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def run_query(payload: QueryRequest) -> QueryResponse:
    """Execute an end-to-end query workflow."""

    started = perf_counter()
    ingesters = []
    if "twitter" in payload.sources:
        ingesters.append(TwitterIngester())
    if "reddit" in payload.sources:
        ingesters.append(RedditIngester())

    posts = []
    for ingester in ingesters:
        posts.extend(
            await ingester.fetch(payload.topic, payload.window_hours, payload.limit)
        )

    scorer = RoBERTaSentimentScorer()
    sentiments = await scorer.batch_score([post.text for post in posts])

    weighter = EngagementWeighter()
    weighted = weighter.apply_weights(posts, sentiments)

    timeline_service = TimelineAggregator()
    timeline_result = timeline_service.build_timeline(posts, sentiments, bucket="hour")

    divergence_detector = DivergenceDetector()
    divergence_flags = divergence_detector.build_explanations(weighted)

    result = QueryResponse(
        query_id=str(uuid4()),
        topic=payload.topic,
        sources=[source for source in payload.sources],
        window_hours=payload.window_hours,
        weighted_result=weighted,
        timeline=timeline_result.buckets,
        divergence_flags=divergence_flags,
        runtime_ms=round((perf_counter() - started) * 1000.0, 2),
        queried_at=datetime.now(timezone.utc),
    )
    query_cache.set(result.query_id, result)
    return result


@router.get("/{query_id}", response_model=CachedQueryResponse)
async def get_cached_query(query_id: str) -> CachedQueryResponse:
    """Return a cached query result by ID."""

    query = query_cache.get(query_id)
    if query is None:
        return CachedQueryResponse(found=False, query=None)
    return CachedQueryResponse(found=True, query=query)

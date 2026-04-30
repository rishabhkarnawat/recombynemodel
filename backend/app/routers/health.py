"""Health and key validation routes."""

from app.config import settings
from app.schemas.post import (
    HealthStatus,
    KeyValidationRequest,
    KeyValidationResponse,
    KeyValidationResult,
)
from app.services.ingestion.reddit import RedditIngester
from app.services.ingestion.twitter import TwitterIngester
from app.services.scoring.roberta import RoBERTaSentimentScorer
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=HealthStatus)
async def get_health() -> HealthStatus:
    """Return service health and key readiness."""

    scorer = RoBERTaSentimentScorer()
    return HealthStatus(
        status="ok" if settings.get_available_sources() else "degraded",
        available_sources=settings.get_available_sources(),
        model_loaded=scorer.is_model_ready(),
        source_key_status={
            "twitter": TwitterIngester().validate_credentials(),
            "reddit": RedditIngester().validate_credentials(),
        },
    )


@router.post("/api/keys/validate", response_model=KeyValidationResponse)
async def validate_keys(payload: KeyValidationRequest) -> KeyValidationResponse:
    """Validate candidate API credentials against source APIs."""

    twitter_result = TwitterIngester().validate_credentials_with_override(
        payload.twitter_bearer_token
    )
    reddit_result = RedditIngester().validate_credentials_with_override(
        payload.reddit_client_id,
        payload.reddit_client_secret,
        payload.reddit_user_agent,
    )
    return KeyValidationResponse(
        results=[
            KeyValidationResult(
                source="twitter", valid=twitter_result[0], reason=twitter_result[1]
            ),
            KeyValidationResult(
                source="reddit", valid=reddit_result[0], reason=reddit_result[1]
            ),
        ]
    )

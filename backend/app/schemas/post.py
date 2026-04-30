"""Post-related request and response schemas."""

from datetime import datetime
from typing import Literal

from app.schemas.sentiment import TimelineBucket, WeightedResult
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request payload for running a sentiment intelligence query."""

    topic: str = Field(min_length=1)
    sources: list[Literal["twitter", "reddit"]] = Field(
        default_factory=lambda: ["twitter", "reddit"]
    )
    window_hours: int = Field(default=168, ge=1, le=2160)
    limit: int = Field(default=500, ge=1, le=2000)


class QueryResponse(BaseModel):
    """Response payload returned from the query endpoint."""

    query_id: str
    topic: str
    sources: list[str]
    window_hours: int
    weighted_result: WeightedResult
    timeline: list[TimelineBucket]
    divergence_flags: list[str]
    runtime_ms: float
    queried_at: datetime


class CachedQueryResponse(BaseModel):
    """Response model for cached query retrieval."""

    found: bool
    query: QueryResponse | None


class KeyValidationRequest(BaseModel):
    """Optional user-supplied API keys for validation endpoint."""

    twitter_bearer_token: str | None = None
    reddit_client_id: str | None = None
    reddit_client_secret: str | None = None
    reddit_user_agent: str | None = None


class KeyValidationResult(BaseModel):
    """Individual source validation result."""

    source: Literal["twitter", "reddit"]
    valid: bool
    reason: str


class KeyValidationResponse(BaseModel):
    """Response containing key validation outcomes."""

    results: list[KeyValidationResult]


class HealthStatus(BaseModel):
    """API health status and dependency readiness details."""

    status: Literal["ok", "degraded"]
    available_sources: list[Literal["twitter", "reddit"]]
    model_loaded: bool
    source_key_status: dict[str, bool]

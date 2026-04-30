"""Post-related request and response schemas."""

from datetime import datetime
from typing import Literal

from app.schemas.sentiment import (
    CoMention,
    DivergenceFlag,
    TimelineBucket,
    WeightedResult,
)
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
    structured_divergence_flags: list[DivergenceFlag] = Field(default_factory=list)
    co_mentions: list[CoMention] = Field(default_factory=list)
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


class WatchlistEntryRequest(BaseModel):
    """Payload for creating a watchlist topic."""

    topic: str = Field(min_length=1)
    sources: list[Literal["twitter", "reddit"]] = Field(
        default_factory=lambda: ["twitter", "reddit"]
    )
    window_hours: int = Field(default=168, ge=1, le=2160)
    refresh_interval_minutes: int = Field(default=60, ge=5, le=24 * 60)


class WatchlistEntry(BaseModel):
    """Watchlist topic with refresh metadata."""

    id: str
    topic: str
    sources: list[Literal["twitter", "reddit"]]
    window_hours: int
    refresh_interval_minutes: int
    last_refreshed_at: datetime | None
    last_weighted_score: float | None
    delta_since_last: float | None
    created_at: datetime


class WatchlistResponse(BaseModel):
    """Watchlist listing response."""

    entries: list[WatchlistEntry]


class HistoryEntry(BaseModel):
    """Compact history entry returned to dashboards and CLIs."""

    id: str
    topic: str
    sources: list[str]
    window_hours: int
    raw_score: float
    weighted_score: float
    divergence: float
    divergence_flag: bool
    post_count: int
    queried_at: datetime
    runtime_ms: float


class HistoryResponse(BaseModel):
    """Paginated history listing of past queries."""

    entries: list[HistoryEntry]

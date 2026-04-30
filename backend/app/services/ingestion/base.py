"""Base abstractions for social ingestion providers."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class EngagementMetrics(BaseModel):
    """Raw engagement counters from a social platform."""

    likes: int = Field(default=0, ge=0)
    reposts: int = Field(default=0, ge=0)
    comments: int = Field(default=0, ge=0)
    views: int | None = Field(default=None, ge=0)
    upvote_ratio: float | None = Field(default=None, ge=0.0, le=1.0)


class RawPost(BaseModel):
    """Normalized raw social post representation across sources."""

    id: str
    source: Literal["twitter", "reddit"]
    text: str
    author: str
    created_at: datetime
    url: str
    raw_engagement: EngagementMetrics
    metadata: dict


class RecombyneFetchError(Exception):
    """Raised when ingestion cannot fetch data from a provider."""


class BaseIngester(ABC):
    """Abstract contract for data source ingesters."""

    @abstractmethod
    async def fetch(self, query: str, window_hours: int, limit: int) -> list[RawPost]:
        """Fetch a batch of posts for a query window."""

    @abstractmethod
    async def stream(self, query: str, callback: Callable) -> None:
        """Stream query results and emit posts via callback."""

    @abstractmethod
    def validate_credentials(self) -> bool:
        """Validate source credentials from environment configuration."""

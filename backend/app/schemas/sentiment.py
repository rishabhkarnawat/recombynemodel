"""Sentiment and weighting output schemas."""

from datetime import datetime
from typing import Literal

from app.services.ingestion.base import RawPost
from pydantic import BaseModel, Field


class SentimentResult(BaseModel):
    """Sentiment output for a single post."""

    label: Literal["positive", "neutral", "negative"]
    score: float = Field(ge=-1.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    raw_logits: list[float]


class TopSignal(BaseModel):
    """Highest impact posts after engagement weighting."""

    post: RawPost
    sentiment: SentimentResult
    weight: float
    signal_strength: float


class WeightedResult(BaseModel):
    """Aggregate sentiment outcome with engagement weighting."""

    raw_score: float
    weighted_score: float
    total_posts: int
    total_weighted_posts: float
    divergence: float
    divergence_flag: bool
    divergence_direction: Literal["weighted_positive", "weighted_negative", "aligned"]
    top_signals: list[TopSignal]


class TimelineBucket(BaseModel):
    """Time bucket representing sentiment movement over time."""

    timestamp: datetime
    raw_score: float
    weighted_score: float
    post_count: int
    dominant_label: Literal["positive", "neutral", "negative"]


class TimelineResult(BaseModel):
    """Timeline response with trend direction metadata."""

    buckets: list[TimelineBucket]
    trend_direction: Literal["surging", "rising", "flat", "falling", "crashing"]

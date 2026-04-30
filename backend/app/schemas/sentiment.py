"""Sentiment and weighting output schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.services.ingestion.base import RawPost


class SentimentResult(BaseModel):
    """Sentiment output for a single post."""

    label: Literal["positive", "neutral", "negative"]
    score: float = Field(ge=-1.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    raw_logits: list[float]
    negation_detected: bool = False
    sarcasm_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    is_english: bool = True


class TopSignal(BaseModel):
    """Highest impact posts after engagement weighting."""

    post: RawPost
    sentiment: SentimentResult
    weight: float
    signal_strength: float


class DivergenceFlag(BaseModel):
    """Structured divergence flag describing why and how strongly we noticed it."""

    type: Literal[
        "weighted_vs_raw",
        "platform",
        "temporal",
        "volume",
    ]
    severity: Literal["low", "medium", "high"]
    explanation: str


class CoMention(BaseModel):
    """Entity co-mentioned alongside the queried topic."""

    entity: str
    mention_count: int
    weighted_mention_count: float
    avg_sentiment_when_mentioned: float
    sentiment_direction: Literal[
        "positive_association", "negative_association", "neutral"
    ]


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
    low_confidence_post_count: int = 0
    non_english_post_count: int = 0


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

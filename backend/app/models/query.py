"""Persistence model for executed query results."""

from datetime import datetime, timezone

from app.models.sentiment import Base
from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column


class QueryRecord(Base):
    """Persistent record for an executed Recombyne query."""

    __tablename__ = "queries"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    topic: Mapped[str] = mapped_column(String(255), index=True)
    sources: Mapped[list] = mapped_column(JSON, default=list)
    window_hours: Mapped[int] = mapped_column(Integer, default=168)
    raw_score: Mapped[float] = mapped_column(Float, default=0.0)
    weighted_score: Mapped[float] = mapped_column(Float, default=0.0)
    divergence: Mapped[float] = mapped_column(Float, default=0.0)
    divergence_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    post_count: Mapped[int] = mapped_column(Integer, default=0)
    queried_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    runtime_ms: Mapped[float] = mapped_column(Float, default=0.0)
    full_result: Mapped[dict] = mapped_column(JSON, default=dict)

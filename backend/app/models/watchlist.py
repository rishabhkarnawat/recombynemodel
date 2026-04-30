"""Persistence model for the topic watchlist."""

from datetime import datetime, timezone

from app.models.sentiment import Base
from sqlalchemy import JSON, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column


class WatchlistRecord(Base):
    """Tracked topic with refresh metadata."""

    __tablename__ = "watchlist"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    topic: Mapped[str] = mapped_column(String(255), index=True)
    sources: Mapped[list] = mapped_column(JSON, default=list)
    window_hours: Mapped[int] = mapped_column(Integer, default=168)
    refresh_interval_minutes: Mapped[int] = mapped_column(Integer, default=60)
    last_refreshed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_weighted_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    delta_since_last: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

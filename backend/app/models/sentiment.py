"""Sentiment model and shared SQLAlchemy base."""

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all database models."""


class Sentiment(Base):
    """Stores sentiment scores for ingested posts."""

    __tablename__ = "sentiments"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    post_id: Mapped[str] = mapped_column(ForeignKey("posts.id"), index=True)
    score: Mapped[float] = mapped_column(Float())
    confidence: Mapped[float] = mapped_column(Float())

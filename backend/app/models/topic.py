"""Topic model placeholder for tracked queries."""

from app.models.sentiment import Base
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class Topic(Base):
    """Persisted topic definition."""

    __tablename__ = "topics"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)

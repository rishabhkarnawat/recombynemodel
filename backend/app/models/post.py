"""Post model placeholder for future SQLAlchemy integration."""

from app.models.sentiment import Base
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column


class Post(Base):
    """Persisted social post entity."""

    __tablename__ = "posts"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    source: Mapped[str] = mapped_column(String(32), index=True)
    text: Mapped[str] = mapped_column(Text())

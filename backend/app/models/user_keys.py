"""User key metadata model placeholder."""

from app.models.sentiment import Base
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column


class UserKey(Base):
    """Persisted key validation state without storing raw secrets."""

    __tablename__ = "user_keys"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    source: Mapped[str] = mapped_column(String(32), unique=True)
    is_valid: Mapped[bool] = mapped_column(Boolean(), default=False)

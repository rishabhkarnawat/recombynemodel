"""Standardized exception hierarchy for the Recombyne backend.

Every domain failure should raise one of these typed exceptions instead of
generic Python errors so the API layer can return consistent JSON payloads.
"""

from __future__ import annotations

from typing import Any


class RecombynError(Exception):
    """Base exception for all Recombyne domain errors.

    Attributes:
        code: Stable machine-readable error code.
        message: Human readable error message.
        docs_url: Optional documentation pointer for resolution steps.
        context: Optional dict with extra debugging context.
    """

    code: str = "RECOMBYNE_ERROR"
    docs_url: str | None = None

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        docs_url: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: User-facing message.
            code: Optional machine-readable code override.
            docs_url: Optional documentation pointer.
            context: Optional extra debug context.
        """

        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        if docs_url:
            self.docs_url = docs_url
        self.context = context or {}


class RecombyneFetchError(RecombynError):
    """Raised when ingestion cannot fetch data from a provider."""

    code = "RECOMBYNE_FETCH_ERROR"
    docs_url = (
        "https://github.com/rishabhkarnawat/recombynemodel/blob/main/docs/byoa-setup.md"
    )


class RecombyneScoringError(RecombynError):
    """Raised when the sentiment scoring pipeline fails."""

    code = "RECOMBYNE_SCORING_ERROR"


class RecombyneDatabaseError(RecombynError):
    """Raised on database persistence failures."""

    code = "RECOMBYNE_DB_ERROR"


class RecombynKeyError(RecombynError):
    """Raised when API keys are missing or invalid."""

    code = "RECOMBYNE_KEY_ERROR"
    docs_url = (
        "https://github.com/rishabhkarnawat/recombynemodel/blob/main/docs/byoa-setup.md"
    )


class RecombynRateLimitError(RecombynError):
    """Raised when an upstream provider rate limit is hit.

    Attributes:
        retry_after: Seconds clients should wait before retrying.
    """

    code = "RECOMBYNE_RATE_LIMIT"

    def __init__(
        self,
        message: str,
        *,
        retry_after: int = 60,
        code: str | None = None,
        docs_url: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a rate limit error with a retry hint."""

        super().__init__(message, code=code, docs_url=docs_url, context=context)
        self.retry_after = int(retry_after)


__all__: list[str] = [
    "RecombynError",
    "RecombyneFetchError",
    "RecombyneScoringError",
    "RecombyneDatabaseError",
    "RecombynKeyError",
    "RecombynRateLimitError",
]

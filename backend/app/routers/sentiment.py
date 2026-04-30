"""Sentiment-focused routes."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/sentiment", tags=["sentiment"])


@router.get("/labels")
async def get_labels() -> dict[str, list[str]]:
    """Return available sentiment labels."""

    return {"labels": ["positive", "neutral", "negative"]}

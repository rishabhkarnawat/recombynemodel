"""Ingestion-specific routes."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/ingest", tags=["ingest"])


@router.get("/sources")
async def list_sources() -> dict[str, list[str]]:
    """Return supported ingestion source names."""

    return {"sources": ["twitter", "reddit"]}

"""FastAPI entrypoint for the Recombyne backend."""

from __future__ import annotations

from app.config import settings
from app.routers import health, ingest, query, sentiment, watchlist
from app.utils.errors import (
    RecombyneDatabaseError,
    RecombyneFetchError,
    RecombynError,
    RecombyneScoringError,
    RecombynKeyError,
    RecombynRateLimitError,
)
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Recombyne API",
    description=(
        "Engagement-weighted sentiment intelligence. Signal from the scatter."
    ),
    version="0.2.0",
    openapi_tags=[
        {"name": "Query", "description": "Run sentiment intelligence queries."},
        {"name": "Watchlist", "description": "Track topics on a refresh schedule."},
        {"name": "Ingestion", "description": "Source ingestion utilities."},
        {"name": "Health", "description": "Service health and key validation."},
        {"name": "Sentiment", "description": "Sentiment metadata helpers."},
    ],
    contact={
        "name": "Recombyne",
        "url": "https://github.com/rishabhkarnawat/recombynemodel",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _build_error_payload(exc: RecombynError) -> dict:
    """Return the structured JSON body for a Recombyne domain error."""

    payload = {
        "error": exc.__class__.__name__,
        "message": exc.message,
        "code": exc.code,
        "docs": exc.docs_url,
    }
    if exc.context:
        payload["context"] = exc.context
    if isinstance(exc, RecombynRateLimitError):
        payload["retry_after"] = exc.retry_after
    return payload


@app.exception_handler(RecombynError)
async def handle_recombyne_error(_: Request, exc: RecombynError) -> JSONResponse:
    """Translate Recombyne domain errors into structured JSON responses."""

    status_code = 500
    if isinstance(exc, RecombynRateLimitError):
        status_code = 429
    elif isinstance(exc, RecombynKeyError):
        status_code = 401
    elif isinstance(exc, RecombyneFetchError):
        status_code = 502
    elif isinstance(exc, RecombyneScoringError):
        status_code = 503
    elif isinstance(exc, RecombyneDatabaseError):
        status_code = 500
    return JSONResponse(status_code=status_code, content=_build_error_payload(exc))


app.include_router(health.router)
app.include_router(query.router)
app.include_router(watchlist.router)
app.include_router(sentiment.router)
app.include_router(ingest.router)

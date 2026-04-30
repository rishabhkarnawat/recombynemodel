"""FastAPI entrypoint for the Recombyne backend."""

from app.config import settings
from app.routers import health, ingest, query, sentiment
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Recombyne API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(query.router)
app.include_router(sentiment.router)
app.include_router(ingest.router)

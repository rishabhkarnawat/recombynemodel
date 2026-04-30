# Recombyne API Reference

This page documents the HTTP API exposed by `backend/app/main.py`. The
interactive OpenAPI surface is also available at `/docs` once the backend is
running.

## Conventions

- All requests and responses use JSON unless noted.
- Errors use a structured payload defined in `backend/app/utils/errors.py`:
  ```json
  {
    "error": "RecombyneFetchError",
    "message": "Twitter API returned 401. Your Bearer Token may be expired.",
    "code": "TWITTER_AUTH_FAILED",
    "docs": "https://github.com/rishabhkarnawat/recombynemodel/blob/main/docs/byoa-setup.md"
  }
  ```

## Endpoints

### POST `/api/query`
Run an end-to-end sentiment intelligence query.

**Request body**
```json
{
  "topic": "NVDA",
  "sources": ["twitter", "reddit"],
  "window_hours": 168,
  "limit": 500
}
```

**Response**: [`QueryResponse`](../backend/app/schemas/post.py).

### GET `/api/query/{query_id}`
Return a previously executed query result by ID.

### GET `/api/query/history?limit=20`
List recent queries served by the local history store.

### GET `/api/query/{query_id}/export?format=csv`
Export a query as CSV (one row per top signal post) or JSON (full WeightedResult).

### POST `/api/watchlist`
Add a tracked topic with refresh metadata.

### GET `/api/watchlist`
List watchlist entries with their last refresh outcome.

### POST `/api/watchlist/refresh`
Schedule background refresh sweeps for entries whose interval has elapsed.

### DELETE `/api/watchlist/{entry_id}`
Remove a watchlist entry.

### GET `/api/health`
Return health, model load status, and key validation results.

### POST `/api/keys/validate`
Validate provided Twitter and Reddit credentials.

### GET `/api/sentiment/labels`
Return the supported sentiment labels.

### GET `/api/ingest/sources`
Return the supported ingestion sources.

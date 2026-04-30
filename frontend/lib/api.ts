import { API_BASE_URL } from "@/lib/constants";
import {
  CachedQueryResponse,
  HealthStatus,
  HistoryResponse,
  KeyValidationRequest,
  KeyValidationResponse,
  QueryRequest,
  QueryResponse,
  WatchlistEntry,
  WatchlistEntryRequest,
  WatchlistResponse,
} from "@/lib/types";

/**
 * Send a typed JSON request to the backend API.
 * @param path Route path.
 * @param options Fetch options.
 * @returns Typed response payload.
 */
async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Recombyne API error (${response.status}): ${body || "Unknown error"}`);
  }
  return (await response.json()) as T;
}

/**
 * Run a sentiment intelligence query.
 * @param payload Query request payload.
 * @returns Query response payload.
 */
export function postQuery(payload: QueryRequest): Promise<QueryResponse> {
  return request<QueryResponse>("/api/query", { method: "POST", body: JSON.stringify(payload) });
}

/**
 * Fetch a cached query by query ID.
 * @param queryId Query ID to resolve.
 * @returns Cached query response wrapper.
 */
export function getQuery(queryId: string): Promise<CachedQueryResponse> {
  return request<CachedQueryResponse>(`/api/query/${queryId}`);
}

/**
 * Fetch the recent query history.
 * @param limit Maximum number of entries to return.
 * @returns History listing response.
 */
export function getHistory(limit = 20): Promise<HistoryResponse> {
  return request<HistoryResponse>(`/api/query/history?limit=${limit}`);
}

/**
 * Build the export URL for a query result.
 * @param queryId Query ID to export.
 * @param format "json" or "csv".
 * @returns Fully qualified export URL.
 */
export function getExportUrl(queryId: string, format: "json" | "csv"): string {
  return `${API_BASE_URL}/api/query/${queryId}/export?format=${format}`;
}

/**
 * Fetch backend health metadata.
 * @returns Health status payload.
 */
export function getHealth(): Promise<HealthStatus> {
  return request<HealthStatus>("/api/health");
}

/**
 * Validate BYOA credentials for supported sources.
 * @param payload Key validation payload.
 * @returns Validation result per source.
 */
export function validateKeys(payload: KeyValidationRequest): Promise<KeyValidationResponse> {
  return request<KeyValidationResponse>("/api/keys/validate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/**
 * Fetch all watchlist entries.
 * @returns Watchlist listing response.
 */
export function getWatchlist(): Promise<WatchlistResponse> {
  return request<WatchlistResponse>("/api/watchlist");
}

/**
 * Add a topic to the watchlist.
 * @param payload Watchlist creation request.
 * @returns Newly created watchlist entry.
 */
export function addWatchlistEntry(payload: WatchlistEntryRequest): Promise<WatchlistEntry> {
  return request<WatchlistEntry>("/api/watchlist", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/**
 * Remove a watchlist entry.
 * @param entryId Watchlist entry ID.
 * @returns Removal confirmation payload.
 */
export function removeWatchlistEntry(entryId: string): Promise<{ removed: boolean }> {
  return request<{ removed: boolean }>(`/api/watchlist/${entryId}`, { method: "DELETE" });
}

/**
 * Trigger a watchlist refresh sweep on the backend.
 * @returns Number of entries scheduled for refresh.
 */
export function triggerWatchlistRefresh(): Promise<{ scheduled: number }> {
  return request<{ scheduled: number }>("/api/watchlist/refresh", { method: "POST" });
}

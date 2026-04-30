import { API_BASE_URL } from "@/lib/constants";
import { CachedQueryResponse, HealthStatus, KeyValidationRequest, KeyValidationResponse, QueryRequest, QueryResponse } from "@/lib/types";

/**
 * Send a typed request to the backend API.
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
  return request<KeyValidationResponse>("/api/keys/validate", { method: "POST", body: JSON.stringify(payload) });
}

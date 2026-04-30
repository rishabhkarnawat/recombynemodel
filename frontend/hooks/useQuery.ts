"use client";

import { useState } from "react";
import { postQuery } from "@/lib/api";
import type { QueryRequest, QueryResponse } from "@/lib/types";

/**
 * Manage query execution state for dashboard interactions.
 * @returns Query state plus runQuery action and a setter for cached results.
 */
export function useQuery() {
  const [data, setData] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Execute backend query and update local state.
   * @param payload Query request payload.
   */
  const runQuery = async (payload: QueryRequest) => {
    setLoading(true);
    setError(null);
    try {
      const result = await postQuery(payload);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run query.");
    } finally {
      setLoading(false);
    }
  };

  return { data, loading, error, runQuery, setData };
}

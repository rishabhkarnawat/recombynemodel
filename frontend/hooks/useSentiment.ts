import { useMemo } from "react";
import { QueryResponse } from "@/lib/types";

/**
 * Derive sentiment-focused view model from query responses.
 * @param data Query response data.
 * @returns Memoized sentiment summary object.
 */
export function useSentiment(data: QueryResponse | null) {
  return useMemo(() => {
    if (!data) {
      return { label: "neutral", score: 0 };
    }
    const score = data.weighted_result.weighted_score;
    const label = score > 0.1 ? "positive" : score < -0.1 ? "negative" : "neutral";
    return { label, score };
  }, [data]);
}

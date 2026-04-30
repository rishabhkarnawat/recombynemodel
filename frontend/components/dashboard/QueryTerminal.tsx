"use client";

import { useEffect, useMemo, useState } from "react";
import { QueryResponse } from "@/lib/types";

/**
 * Renders query lifecycle output in a terminal-like animated view.
 * @param props Query execution context and response payload.
 * @returns CLI-style animated output panel.
 */
export function QueryTerminal({ topic, data, loading, error, windowHours, sources }: { topic: string; data: QueryResponse | null; loading: boolean; error: string | null; windowHours: number; sources: Array<"twitter" | "reddit">; }) {
  const lines = useMemo(() => {
    const windowDays = Math.max(1, Math.round(windowHours / 24));
    const weightedLabel = data ? (data.weighted_result.weighted_score > 0.1 ? "positive" : data.weighted_result.weighted_score < -0.1 ? "negative" : "neutral") : "neutral";
    const arrow = data && data.weighted_result.weighted_score >= data.weighted_result.raw_score ? "↑" : "↓";
    return [
      `Recombyne CLI  |  Querying: "${topic}"`,
      `Sources: ${sources.join(", ") || "none"}`,
      `Time window: last ${windowDays} days`,
      "────────────────────────────────────────",
      `Ingesting ${data?.weighted_result.total_posts ?? 0} posts...`,
      "Scoring with sentiment engine (RoBERTa)...",
      "Applying engagement weight...",
      "────────────────────────────────────────",
      "SENTIMENT SUMMARY",
      `  Overall score:     ${data?.weighted_result.raw_score.toFixed(3) ?? "0.000"}  (${weightedLabel})`,
      `  Confidence:        ${data ? Math.round((Math.abs(data.weighted_result.raw_score) + Math.abs(data.weighted_result.weighted_score)) * 50) : 0}%`,
      `  Weighted score:    ${data?.weighted_result.weighted_score.toFixed(3) ?? "0.000"}  (${arrow} ${weightedLabel})`,
      "  Trend direction:   flat",
      "",
      "TOP SIGNALS",
      ...(data?.weighted_result.top_signals.map((item, index) => `  ${index + 1}. [${item.post.source}] ${item.sentiment.score.toFixed(3)} | ${item.post.text.slice(0, 60)}`) ?? ["  ..."]),
      "",
      `DIVERGENCE FLAG: ${data?.weighted_result.divergence_flag ? data.divergence_flags[0] ?? "Flagged" : "none"}`,
      "────────────────────────────────────────",
      `Query complete.  |  Runtime: ${data?.runtime_ms ?? 0}ms`,
      error ? `ERROR: ${error}` : "",
      loading ? "Running query..." : "",
    ].filter(Boolean);
  }, [data, error, loading, sources, topic, windowHours]);

  const [visibleLines, setVisibleLines] = useState(0);

  useEffect(() => {
    setVisibleLines(0);
    const timer = setInterval(() => {
      setVisibleLines((value) => {
        if (value >= lines.length) {
          clearInterval(timer);
          return value;
        }
        return value + 1;
      });
    }, 300);
    return () => clearInterval(timer);
  }, [lines]);

  return <pre className="overflow-auto rounded border border-slate-800 bg-black p-4 font-mono text-xs text-emerald-300">{lines.slice(0, visibleLines).join("\n")}</pre>;
}

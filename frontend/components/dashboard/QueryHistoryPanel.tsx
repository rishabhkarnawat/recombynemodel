"use client";

import { useEffect, useState } from "react";
import { getHistory, getQuery } from "@/lib/api";
import type { HistoryEntry, QueryResponse } from "@/lib/types";

/**
 * Sidebar panel that lists the most recent queries and lets the user
 * jump to any past result without rerunning the pipeline.
 *
 * @param props Component props.
 * @returns React element rendering the recent queries list.
 */
export function QueryHistoryPanel({
  onSelect,
  refreshSignal,
}: {
  onSelect: (response: QueryResponse) => void;
  refreshSignal?: number;
}) {
  const [entries, setEntries] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      try {
        const result = await getHistory(20);
        if (!cancelled) setEntries(result.entries);
      } catch (error) {
        console.warn("history fetch failed", error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [refreshSignal]);

  const handleClick = async (entry: HistoryEntry) => {
    try {
      const cached = await getQuery(entry.id);
      if (cached.found && cached.query) {
        onSelect(cached.query);
      }
    } catch (error) {
      console.warn("history click failed", error);
    }
  };

  return (
    <aside className="rounded border border-slate-800 bg-slate-900 p-3 text-sm">
      <h2 className="mb-2 text-xs font-semibold uppercase text-slate-400">Query History</h2>
      {loading ? <p className="text-xs text-slate-500">Loading...</p> : null}
      {entries.length === 0 && !loading ? (
        <p className="text-xs text-slate-500">No queries yet. Run one to populate this panel.</p>
      ) : null}
      <ul className="space-y-2">
        {entries.map((entry) => (
          <li key={entry.id}>
            <button
              type="button"
              onClick={() => handleClick(entry)}
              className="w-full rounded border border-slate-800 bg-slate-950 p-2 text-left hover:border-emerald-700"
            >
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>{entry.topic}</span>
                <span>{entry.weighted_score.toFixed(3)}</span>
              </div>
              <p className="text-[10px] text-slate-500">{new Date(entry.queried_at).toLocaleString()}</p>
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
}

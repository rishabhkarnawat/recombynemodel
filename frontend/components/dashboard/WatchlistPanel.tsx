"use client";

import { useEffect, useState } from "react";
import {
  addWatchlistEntry,
  getWatchlist,
  removeWatchlistEntry,
  triggerWatchlistRefresh,
} from "@/lib/api";
import type { WatchlistEntry } from "@/lib/types";

/**
 * Watchlist panel for tracking topics on a recurring schedule.
 * Renders existing entries with delta indicators and provides a quick add-action.
 *
 * @param props Component props.
 * @returns React element representing the watchlist panel.
 */
export function WatchlistPanel({
  initialTopic,
  initialSources,
  initialWindowHours,
}: {
  initialTopic?: string;
  initialSources: Array<"twitter" | "reddit">;
  initialWindowHours: number;
}) {
  const [entries, setEntries] = useState<WatchlistEntry[]>([]);
  const [loading, setLoading] = useState(false);

  const reload = async () => {
    setLoading(true);
    try {
      const result = await getWatchlist();
      setEntries(result.entries);
    } catch (error) {
      console.warn("watchlist fetch failed", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void reload();
  }, []);

  const handleAdd = async () => {
    if (!initialTopic) return;
    try {
      await addWatchlistEntry({
        topic: initialTopic,
        sources: initialSources.length ? initialSources : ["twitter", "reddit"],
        window_hours: initialWindowHours,
        refresh_interval_minutes: 60,
      });
      await reload();
    } catch (error) {
      console.warn("watchlist add failed", error);
    }
  };

  const handleRemove = async (id: string) => {
    try {
      await removeWatchlistEntry(id);
      await reload();
    } catch (error) {
      console.warn("watchlist remove failed", error);
    }
  };

  const handleRefresh = async () => {
    try {
      await triggerWatchlistRefresh();
    } catch (error) {
      console.warn("watchlist refresh failed", error);
    }
  };

  return (
    <section className="rounded border border-slate-800 bg-slate-900 p-3 text-sm">
      <header className="mb-2 flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase text-slate-400">Watchlist</h2>
        <div className="flex gap-2 text-xs">
          <button
            type="button"
            onClick={handleAdd}
            disabled={!initialTopic}
            className="rounded bg-emerald-700 px-2 py-1 disabled:opacity-50"
          >
            Track current topic
          </button>
          <button
            type="button"
            onClick={handleRefresh}
            className="rounded bg-slate-700 px-2 py-1"
          >
            Refresh
          </button>
        </div>
      </header>
      {loading ? <p className="text-xs text-slate-500">Loading...</p> : null}
      {entries.length === 0 && !loading ? (
        <p className="text-xs text-slate-500">No tracked topics yet.</p>
      ) : null}
      <ul className="space-y-2">
        {entries.map((entry) => {
          const score = entry.last_weighted_score;
          const delta = entry.delta_since_last;
          const directionIcon = delta == null ? "·" : delta > 0 ? "↑" : delta < 0 ? "↓" : "→";
          return (
            <li key={entry.id} className="rounded border border-slate-800 bg-slate-950 p-2">
              <div className="flex items-center justify-between text-sm">
                <span>{entry.topic}</span>
                <span className="text-xs text-slate-400">
                  {score == null ? "n/a" : score.toFixed(3)} {directionIcon}
                  {delta == null ? "" : delta.toFixed(3)}
                </span>
              </div>
              <button
                type="button"
                onClick={() => handleRemove(entry.id)}
                className="mt-1 text-[10px] text-slate-500 hover:text-rose-400"
              >
                Remove
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

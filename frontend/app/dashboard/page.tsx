"use client";

import { useMemo, useState } from "react";
import { DivergenceAlert } from "@/components/dashboard/DivergenceAlert";
import { QueryTerminal } from "@/components/dashboard/QueryTerminal";
import { SentimentTimeline } from "@/components/dashboard/SentimentTimeline";
import { TopSignals } from "@/components/dashboard/TopSignals";
import { useQuery } from "@/hooks/useQuery";

/**
 * Main Recombyne dashboard page with query controls and analytics panels.
 * @returns Dashboard UI for running engagement-weighted sentiment queries.
 */
export default function DashboardPage() {
  const [topic, setTopic] = useState("NVDA");
  const [sources, setSources] = useState<Array<"twitter" | "reddit">>(["twitter", "reddit"]);
  const [windowHours, setWindowHours] = useState(24 * 7);
  const { data, loading, error, runQuery } = useQuery();

  const summary = useMemo(() => {
    if (!data) {
      return { raw: 0, weighted: 0, divergence: 0, count: 0 };
    }
    return {
      raw: data.weighted_result.raw_score,
      weighted: data.weighted_result.weighted_score,
      divergence: data.weighted_result.divergence,
      count: data.weighted_result.total_posts,
    };
  }, [data]);

  /**
   * Toggle source inclusion for the query payload.
   * @param source Source name to toggle.
   */
  const toggleSource = (source: "twitter" | "reddit") => {
    setSources((prev) => (prev.includes(source) ? prev.filter((item) => item !== source) : [...prev, source]));
  };

  /**
   * Submit the current query selection to the backend.
   */
  const handleSubmit = async () => {
    await runQuery({ topic, sources, window_hours: windowHours, limit: 500 });
  };

  return (
    <section className="space-y-6">
      <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
        <h1 className="mb-4 text-2xl font-semibold">Recombyne Dashboard</h1>
        <div className="grid gap-3 md:grid-cols-4">
          <input className="rounded border border-slate-700 bg-slate-950 px-3 py-2" value={topic} onChange={(event) => setTopic(event.target.value)} placeholder="Enter a topic..." />
          <div className="flex items-center gap-2 rounded border border-slate-700 bg-slate-950 px-3 py-2">
            <button className={`rounded px-2 py-1 ${sources.includes("twitter") ? "bg-cyan-600" : "bg-slate-800"}`} onClick={() => toggleSource("twitter")}>Twitter</button>
            <button className={`rounded px-2 py-1 ${sources.includes("reddit") ? "bg-orange-600" : "bg-slate-800"}`} onClick={() => toggleSource("reddit")}>Reddit</button>
          </div>
          <select className="rounded border border-slate-700 bg-slate-950 px-3 py-2" value={windowHours} onChange={(event) => setWindowHours(Number(event.target.value))}>
            <option value={24}>24h</option>
            <option value={168}>7d</option>
            <option value={720}>30d</option>
          </select>
          <button className="rounded bg-emerald-600 px-3 py-2 font-medium" onClick={handleSubmit} disabled={loading || sources.length === 0}>
            {loading ? "Running..." : "Run Query"}
          </button>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-4">
        <div className="rounded border border-slate-800 bg-slate-900 p-4">Overall Score: {summary.raw.toFixed(3)}</div>
        <div className="rounded border border-slate-800 bg-slate-900 p-4">Weighted Score: {summary.weighted.toFixed(3)}</div>
        <div className="rounded border border-slate-800 bg-slate-900 p-4">Divergence: {summary.divergence.toFixed(3)}</div>
        <div className="rounded border border-slate-800 bg-slate-900 p-4">Post Count: {summary.count}</div>
      </div>

      {data ? <SentimentTimeline timeline={data.timeline} /> : null}
      {data ? <TopSignals topSignals={data.weighted_result.top_signals} /> : null}
      {data ? <DivergenceAlert weightedResult={data.weighted_result} flags={data.divergence_flags} /> : null}
      <QueryTerminal topic={topic} data={data} loading={loading} error={error} windowHours={windowHours} sources={sources} />
    </section>
  );
}

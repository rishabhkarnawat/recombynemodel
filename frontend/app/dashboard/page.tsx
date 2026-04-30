"use client";

import { useMemo, useState } from "react";

import { CoMentionStrip } from "@/components/dashboard/CoMentionStrip";
import { DivergenceAlert } from "@/components/dashboard/DivergenceAlert";
import { ExportButtons } from "@/components/dashboard/ExportButtons";
import { QueryHistoryPanel } from "@/components/dashboard/QueryHistoryPanel";
import { QueryTerminal } from "@/components/dashboard/QueryTerminal";
import { SentimentTimeline } from "@/components/dashboard/SentimentTimeline";
import { TopSignals } from "@/components/dashboard/TopSignals";
import { WatchlistPanel } from "@/components/dashboard/WatchlistPanel";
import { useQuery } from "@/hooks/useQuery";

/**
 * Main Recombyne dashboard page with query controls and analytics panels.
 * @returns Dashboard UI for running engagement-weighted sentiment queries.
 */
export default function DashboardPage() {
  const [topic, setTopic] = useState("NVDA");
  const [sources, setSources] = useState<Array<"twitter" | "reddit">>(["twitter", "reddit"]);
  const [windowHours, setWindowHours] = useState(24 * 7);
  const [historyTick, setHistoryTick] = useState(0);
  const { data, loading, error, runQuery, setData } = useQuery();

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

  const nonEnglishWarning = useMemo(() => {
    if (!data) return null;
    const total = data.weighted_result.total_posts;
    const nonEnglish = data.weighted_result.non_english_post_count ?? 0;
    if (!total || nonEnglish / total <= 0.1) return null;
    return `${nonEnglish} of ${total} posts were not in English. Sentiment is less reliable for non-English text.`;
  }, [data]);

  const toggleSource = (source: "twitter" | "reddit") => {
    setSources((prev) => (prev.includes(source) ? prev.filter((item) => item !== source) : [...prev, source]));
  };

  const handleSubmit = async () => {
    await runQuery({ topic, sources, window_hours: windowHours, limit: 500 });
    setHistoryTick((value) => value + 1);
  };

  return (
    <section className="grid gap-6 lg:grid-cols-[1fr_280px]">
      <div className="space-y-6">
        <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
          <h1 className="mb-4 text-2xl font-semibold">Recombyne Dashboard</h1>
          <div className="grid gap-3 md:grid-cols-4">
            <input
              className="rounded border border-slate-700 bg-slate-950 px-3 py-2"
              value={topic}
              onChange={(event) => setTopic(event.target.value)}
              placeholder="Enter a topic..."
            />
            <div className="flex items-center gap-2 rounded border border-slate-700 bg-slate-950 px-3 py-2">
              <button
                className={`rounded px-2 py-1 ${sources.includes("twitter") ? "bg-cyan-600" : "bg-slate-800"}`}
                onClick={() => toggleSource("twitter")}
              >
                Twitter
              </button>
              <button
                className={`rounded px-2 py-1 ${sources.includes("reddit") ? "bg-orange-600" : "bg-slate-800"}`}
                onClick={() => toggleSource("reddit")}
              >
                Reddit
              </button>
            </div>
            <select
              className="rounded border border-slate-700 bg-slate-950 px-3 py-2"
              value={windowHours}
              onChange={(event) => setWindowHours(Number(event.target.value))}
            >
              <option value={24}>24h</option>
              <option value={168}>7d</option>
              <option value={720}>30d</option>
            </select>
            <button
              className="rounded bg-emerald-600 px-3 py-2 font-medium"
              onClick={handleSubmit}
              disabled={loading || sources.length === 0}
            >
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

        {data ? <CoMentionStrip coMentions={data.co_mentions ?? []} /> : null}

        {nonEnglishWarning ? (
          <div className="rounded border border-amber-700 bg-amber-900/20 p-3 text-xs text-amber-200">
            {nonEnglishWarning}
          </div>
        ) : null}

        {data ? (
          <div className="flex items-center justify-between rounded border border-slate-800 bg-slate-900 p-3">
            <div className="text-xs text-slate-400">
              Query ID: <span className="text-slate-200">{data.query_id}</span>
            </div>
            <ExportButtons queryId={data.query_id} />
          </div>
        ) : null}

        {data ? <SentimentTimeline timeline={data.timeline} /> : null}
        {data ? <TopSignals topSignals={data.weighted_result.top_signals} /> : null}
        {data ? <DivergenceAlert weightedResult={data.weighted_result} flags={data.divergence_flags} /> : null}
        <QueryTerminal
          topic={topic}
          data={data}
          loading={loading}
          error={error}
          windowHours={windowHours}
          sources={sources}
        />
      </div>

      <div className="space-y-4">
        <QueryHistoryPanel
          refreshSignal={historyTick}
          onSelect={(response) => {
            setData(response);
            setTopic(response.topic);
            setSources(response.sources.filter((source): source is "twitter" | "reddit" => source === "twitter" || source === "reddit"));
            setWindowHours(response.window_hours);
          }}
        />
        <WatchlistPanel
          initialTopic={topic}
          initialSources={sources}
          initialWindowHours={windowHours}
        />
      </div>
    </section>
  );
}

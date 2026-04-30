import { TopSignal } from "@/lib/types";

/**
 * Displays top weighted sentiment signals.
 * @param props Top signal entries.
 * @returns Ranked panel for influential posts.
 */
export function TopSignals({ topSignals }: { topSignals: TopSignal[] }) {
  return (
    <div className="rounded border border-slate-800 bg-slate-900 p-4">
      <h2 className="mb-3 text-lg font-medium">Top Signals</h2>
      <div className="space-y-3">
        {topSignals.map((signal) => (
          <article key={signal.post.id} className="rounded border border-slate-700 bg-slate-950 p-3">
            <div className="mb-1 flex items-center justify-between text-xs uppercase text-slate-400">
              <span>{signal.post.source}</span><span>Signal {signal.signal_strength.toFixed(3)}</span>
            </div>
            <p className="text-sm">{signal.post.text}</p>
            <p className="mt-2 text-xs text-slate-400">Sentiment {signal.sentiment.score.toFixed(3)} | Likes {signal.post.raw_engagement.likes} | Comments {signal.post.raw_engagement.comments}</p>
          </article>
        ))}
      </div>
    </div>
  );
}

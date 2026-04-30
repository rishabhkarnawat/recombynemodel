"use client";

import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { TimelineBucket } from "@/lib/types";

/**
 * Draws raw and weighted sentiment over time.
 * @param props Timeline data props.
 * @returns Recharts line chart.
 */
export function SentimentTimeline({ timeline }: { timeline: TimelineBucket[] }) {
  return (
    <div className="h-80 rounded border border-slate-800 bg-slate-900 p-4">
      <h2 className="mb-2 text-lg font-medium">Sentiment Timeline</h2>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={timeline}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="timestamp" stroke="#94a3b8" />
          <YAxis stroke="#94a3b8" domain={[-1, 1]} />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="raw_score" stroke="#38bdf8" strokeWidth={2} />
          <Line type="monotone" dataKey="weighted_score" stroke="#22c55e" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

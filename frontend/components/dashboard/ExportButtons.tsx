"use client";

import { getExportUrl } from "@/lib/api";

/**
 * Export buttons for the current query result.
 *
 * @param props Component props.
 * @returns React element rendering CSV and JSON export controls.
 */
export function ExportButtons({ queryId }: { queryId: string | null }) {
  if (!queryId) return null;
  return (
    <div className="flex gap-2">
      <a
        className="rounded bg-slate-700 px-3 py-2 text-xs uppercase tracking-wide hover:bg-slate-600"
        href={getExportUrl(queryId, "csv")}
        target="_blank"
        rel="noreferrer"
      >
        Export CSV
      </a>
      <a
        className="rounded bg-slate-700 px-3 py-2 text-xs uppercase tracking-wide hover:bg-slate-600"
        href={getExportUrl(queryId, "json")}
        target="_blank"
        rel="noreferrer"
      >
        Export JSON
      </a>
    </div>
  );
}

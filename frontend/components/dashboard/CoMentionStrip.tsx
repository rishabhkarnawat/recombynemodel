import type { CoMention } from "@/lib/types";

/**
 * Horizontal strip showing top co-mentioned entities for a query.
 *
 * @param props Component props.
 * @returns React element rendering co-mention chips.
 */
export function CoMentionStrip({ coMentions }: { coMentions: CoMention[] }) {
  if (!coMentions || coMentions.length === 0) {
    return null;
  }
  return (
    <div className="flex flex-wrap gap-2 rounded border border-slate-800 bg-slate-900 p-3 text-xs">
      <span className="mr-1 font-semibold uppercase text-slate-400">Co-mentions</span>
      {coMentions.map((entity) => {
        const dotClass =
          entity.sentiment_direction === "positive_association"
            ? "bg-emerald-500"
            : entity.sentiment_direction === "negative_association"
              ? "bg-rose-500"
              : "bg-slate-500";
        return (
          <span
            key={entity.entity}
            className="flex items-center gap-2 rounded-full border border-slate-700 bg-slate-950 px-2 py-1"
          >
            <span className={`h-2 w-2 rounded-full ${dotClass}`} />
            {entity.entity}
            <span className="text-slate-500">({entity.mention_count})</span>
          </span>
        );
      })}
    </div>
  );
}

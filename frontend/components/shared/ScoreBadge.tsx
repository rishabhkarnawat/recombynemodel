/**
 * Render a score value with sign-aware color.
 * @param props Score value prop.
 * @returns Styled score badge.
 */
export function ScoreBadge({ score }: { score: number }) {
  const color = score > 0.1 ? "bg-emerald-700" : score < -0.1 ? "bg-rose-700" : "bg-slate-700";
  return <span className={`rounded px-2 py-1 text-xs ${color}`}>{score.toFixed(3)}</span>;
}

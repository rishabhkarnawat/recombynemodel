/**
 * Show trend direction with directional icon.
 * @param props Direction string.
 * @returns Inline trend indicator.
 */
export function TrendIndicator({ direction }: { direction: string }) {
  const icon = direction === "surging" || direction === "rising" ? "↑" : direction === "flat" ? "→" : "↓";
  return <span className="text-sm">{icon} {direction}</span>;
}

import { WeightedResult } from "@/lib/types";

/**
 * Renders divergence warning when weighted and raw sentiment diverge.
 * @param props Weighted result plus generated flags.
 * @returns Conditional alert banner.
 */
export function DivergenceAlert({ weightedResult, flags }: { weightedResult: WeightedResult; flags: string[] }) {
  if (!weightedResult.divergence_flag) {
    return null;
  }
  return (
    <div className="rounded border border-amber-600 bg-amber-900/20 p-4 text-amber-200">
      <p className="font-semibold">Divergence: {weightedResult.divergence_direction}</p>
      <p>{flags[0] ?? "High-engagement voices diverge from the overall conversation."}</p>
    </div>
  );
}

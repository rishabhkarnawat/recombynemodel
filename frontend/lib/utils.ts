/**
 * Format a score value for concise display.
 * @param value Numeric score.
 * @returns Fixed-precision score string.
 */
export function formatScore(value: number): string {
  return value.toFixed(3);
}

"use client";

import { API_BASE_URL } from "@/lib/constants";

/**
 * Expose frontend runtime settings to components.
 * @returns Object containing selected runtime configuration.
 */
export function useSettings() {
  return { backendUrl: API_BASE_URL };
}

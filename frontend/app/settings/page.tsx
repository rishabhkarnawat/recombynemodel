"use client";

import { useSettings } from "@/hooks/useSettings";

/**
 * Settings route for local client configuration.
 * @returns Settings panel placeholder.
 */
export default function SettingsPage() {
  const { backendUrl } = useSettings();
  return <div className="rounded border border-slate-800 bg-slate-900 p-4">Backend URL: {backendUrl}</div>;
}

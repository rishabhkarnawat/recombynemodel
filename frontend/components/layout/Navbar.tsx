import Link from "next/link";

/**
 * Top navigation for primary routes.
 * @returns Navbar component.
 */
export function Navbar() {
  return (<header className="border-b border-slate-800 bg-slate-900/70"><nav className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4"><span className="font-semibold">Recombyne</span><div className="flex gap-4 text-sm"><Link href="/dashboard">Dashboard</Link><Link href="/query">Query</Link><Link href="/settings">Settings</Link></div></nav></header>);
}

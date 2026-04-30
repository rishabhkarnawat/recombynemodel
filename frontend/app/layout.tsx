import type { Metadata } from "next";
import "./globals.css";
import { Footer } from "@/components/layout/Footer";
import { Navbar } from "@/components/layout/Navbar";
import { Sidebar } from "@/components/layout/Sidebar";

/**
 * Root metadata for the Recombyne frontend app.
 */
export const metadata: Metadata = {
  title: "Recombyne Dashboard",
  description: "Signal from the scatter.",
};

/**
 * Root layout component wrapping all pages with shared navigation.
 * @param props Layout props containing page children.
 * @returns App shell with navbar, sidebar, and footer.
 */
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100">
        <Navbar />
        <div className="mx-auto flex min-h-[calc(100vh-120px)] w-full max-w-7xl gap-6 px-4 py-6">
          <Sidebar />
          <main className="flex-1">{children}</main>
        </div>
        <Footer />
      </body>
    </html>
  );
}

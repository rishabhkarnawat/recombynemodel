import { redirect } from "next/navigation";

/**
 * Redirects the root route to the dashboard experience.
 * @returns Redirect response to /dashboard.
 */
export default function HomePage() {
  redirect("/dashboard");
}

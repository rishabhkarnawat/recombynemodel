import { RawPost } from "@/lib/types";

/**
 * Render a simple list of ingested posts.
 * @param props Component props.
 * @returns Sentiment feed list.
 */
export function SentimentFeed({ posts }: { posts: RawPost[] }) {
  return (<div className="space-y-2">{posts.map((post) => (<article key={post.id} className="rounded border border-slate-800 bg-slate-900 p-3"><p className="text-xs uppercase text-slate-400">{post.source}</p><p className="text-sm">{post.text}</p></article>))}</div>);
}

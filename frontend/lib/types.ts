export interface EngagementMetrics {
  likes: number;
  reposts: number;
  comments: number;
  views: number | null;
  upvote_ratio: number | null;
}

export interface RawPost {
  id: string;
  source: "twitter" | "reddit";
  text: string;
  author: string;
  created_at: string;
  url: string;
  raw_engagement: EngagementMetrics;
  metadata: Record<string, unknown>;
}

export interface SentimentResult {
  label: "positive" | "neutral" | "negative";
  score: number;
  confidence: number;
  raw_logits: number[];
}

export interface TopSignal {
  post: RawPost;
  sentiment: SentimentResult;
  weight: number;
  signal_strength: number;
}

export interface WeightedResult {
  raw_score: number;
  weighted_score: number;
  total_posts: number;
  total_weighted_posts: number;
  divergence: number;
  divergence_flag: boolean;
  divergence_direction: "weighted_positive" | "weighted_negative" | "aligned";
  top_signals: TopSignal[];
}

export interface TimelineBucket {
  timestamp: string;
  raw_score: number;
  weighted_score: number;
  post_count: number;
  dominant_label: "positive" | "neutral" | "negative";
}

export interface TimelineResult {
  buckets: TimelineBucket[];
  trend_direction: "surging" | "rising" | "flat" | "falling" | "crashing";
}

export interface QueryRequest {
  topic: string;
  sources: Array<"twitter" | "reddit">;
  window_hours: number;
  limit: number;
}

export interface QueryResponse {
  query_id: string;
  topic: string;
  sources: string[];
  window_hours: number;
  weighted_result: WeightedResult;
  timeline: TimelineBucket[];
  divergence_flags: string[];
  runtime_ms: number;
  queried_at: string;
}

export interface CachedQueryResponse {
  found: boolean;
  query: QueryResponse | null;
}

export interface KeyValidationRequest {
  twitter_bearer_token?: string | null;
  reddit_client_id?: string | null;
  reddit_client_secret?: string | null;
  reddit_user_agent?: string | null;
}

export interface KeyValidationResult {
  source: "twitter" | "reddit";
  valid: boolean;
  reason: string;
}

export interface KeyValidationResponse {
  results: KeyValidationResult[];
}

export interface HealthStatus {
  status: "ok" | "degraded";
  available_sources: Array<"twitter" | "reddit">;
  model_loaded: boolean;
  source_key_status: Record<string, boolean>;
}

export interface EngagementMetrics {
  likes: number;
  reposts: number;
  comments: number;
  views: number | null;
  upvote_ratio: number | null;
}

export interface AuthorMetrics {
  followers_count?: number | null;
  following_count?: number | null;
  tweet_count?: number | null;
  account_age_days?: number | null;
  verified?: boolean | null;
  comment_karma?: number | null;
  post_karma?: number | null;
}

export interface RawPost {
  id: string;
  source: "twitter" | "reddit";
  text: string;
  author: string;
  created_at: string;
  url: string;
  raw_engagement: EngagementMetrics;
  author_metrics?: AuthorMetrics | null;
  is_english?: boolean | null;
  metadata: Record<string, unknown>;
}

export interface SentimentResult {
  label: "positive" | "neutral" | "negative";
  score: number;
  confidence: number;
  raw_logits: number[];
  negation_detected?: boolean;
  sarcasm_risk?: number;
  is_english?: boolean;
}

export interface TopSignal {
  post: RawPost;
  sentiment: SentimentResult;
  weight: number;
  signal_strength: number;
}

export interface DivergenceFlag {
  type: "weighted_vs_raw" | "platform" | "temporal" | "volume";
  severity: "low" | "medium" | "high";
  explanation: string;
}

export interface CoMention {
  entity: string;
  mention_count: number;
  weighted_mention_count: number;
  avg_sentiment_when_mentioned: number;
  sentiment_direction: "positive_association" | "negative_association" | "neutral";
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
  low_confidence_post_count?: number;
  non_english_post_count?: number;
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
  structured_divergence_flags?: DivergenceFlag[];
  co_mentions?: CoMention[];
  runtime_ms: number;
  queried_at: string;
}

export interface CachedQueryResponse {
  found: boolean;
  query: QueryResponse | null;
}

export interface HistoryEntry {
  id: string;
  topic: string;
  sources: string[];
  window_hours: number;
  raw_score: number;
  weighted_score: number;
  divergence: number;
  divergence_flag: boolean;
  post_count: number;
  queried_at: string;
  runtime_ms: number;
}

export interface HistoryResponse {
  entries: HistoryEntry[];
}

export interface WatchlistEntry {
  id: string;
  topic: string;
  sources: Array<"twitter" | "reddit">;
  window_hours: number;
  refresh_interval_minutes: number;
  last_refreshed_at: string | null;
  last_weighted_score: number | null;
  delta_since_last: number | null;
  created_at: string;
}

export interface WatchlistResponse {
  entries: WatchlistEntry[];
}

export interface WatchlistEntryRequest {
  topic: string;
  sources: Array<"twitter" | "reddit">;
  window_hours: number;
  refresh_interval_minutes: number;
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

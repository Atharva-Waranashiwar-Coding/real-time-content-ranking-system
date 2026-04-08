export const TOPIC_ORDER = ["ai", "backend", "system-design", "devops", "interview-prep"] as const;

export const INTERACTION_EVENT_TYPES = [
  "impression",
  "click",
  "like",
  "save",
  "skip",
  "watch_start",
  "watch_complete",
] as const;

export const SERVICE_KEYS = [
  "feed",
  "user",
  "content",
  "interaction",
  "experimentation",
  "analytics",
] as const;

export type TopicSlug = (typeof TOPIC_ORDER)[number];
export type InteractionEventType = (typeof INTERACTION_EVENT_TYPES)[number];
export type ServiceKey = (typeof SERVICE_KEYS)[number];
export type ContentCategory = TopicSlug;
export type ContentStatus = "draft" | "published";
export type CandidateSource = "recent" | "trending" | "topic_affinity";

export interface HealthCheckResponse {
  status: string;
  service: string;
  version: string;
  timestamp: string;
}

export interface UserProfileResponse {
  id: string;
  user_id: string;
  bio: string | null;
  topic_preferences: Partial<Record<TopicSlug, number>>;
  created_at: string;
  updated_at: string;
}

export interface UserResponse {
  id: string;
  username: string;
  email: string;
  created_at: string;
  updated_at: string;
  profile: UserProfileResponse | null;
}

export interface ContentTagResponse {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface ContentItemResponse {
  id: string;
  title: string;
  description: string | null;
  topic: string;
  category: ContentCategory;
  status: ContentStatus;
  view_count: number;
  engagement_metadata: Record<string, number>;
  created_at: string;
  published_at: string | null;
  updated_at: string;
  tags: ContentTagResponse[];
}

export interface ContentListResponse {
  items: ContentItemResponse[];
  total: number;
  skip: number;
  limit: number;
}

export interface ContentFeaturesResponse {
  schema_name: "content_features.v1";
  content_id: string;
  topic: string | null;
  window_hours: number;
  impressions: number;
  clicks: number;
  likes: number;
  saves: number;
  skip_count: number;
  watch_starts: number;
  watch_completes: number;
  ctr: number;
  like_rate: number;
  save_rate: number;
  skip_rate: number;
  completion_rate: number;
  trending_score: number;
  last_event_at: string | null;
  updated_at: string;
}

export interface RankingScoreBreakdownResponse {
  user_topic_affinity: number;
  user_topic_affinity_weighted: number;
  recency: number;
  recency_weighted: number;
  engagement: number;
  engagement_weighted: number;
  trending: number;
  trending_weighted: number;
  strategy_adjustment: number;
  diversity_penalty: number;
  final_score: number;
}

export interface FeedItemResponse {
  content_id: string;
  title: string;
  description: string | null;
  topic: string;
  category: ContentCategory;
  published_at: string | null;
  candidate_sources: CandidateSource[];
  user_topic_affinity: number;
  content_features: ContentFeaturesResponse;
  rank: number;
  score: number;
  score_breakdown: RankingScoreBreakdownResponse;
}

export interface FeedResponse {
  schema_name: "feed_response.v1";
  user_id: string;
  items: FeedItemResponse[];
  total_candidates: number;
  limit: number;
  offset: number;
  has_more: boolean;
  cache_hit: boolean;
  experiment_assignment: ExperimentAssignmentResponse | null;
  exposure_id: string | null;
  generated_at: string;
}

export interface ExperimentAssignmentResponse {
  schema_name: "experiment_assignment.v1";
  experiment_key: string;
  variant_key: string;
  strategy_name: "rules_v1" | "rules_v2_with_trending_boost";
  user_id: string;
  assignment_bucket: number;
  assigned_at: string;
}

export interface StrategyOutcomeMetricsResponse {
  variant_key: string;
  strategy_name: "rules_v1" | "rules_v2_with_trending_boost";
  exposure_requests: number;
  item_exposures: number;
  unique_users: number;
  clicks: number;
  saves: number;
  completions: number;
  ctr: number;
  save_rate: number;
  completion_rate: number;
}

export interface ExperimentComparisonResponse {
  schema_name: "experiment_comparison.v1";
  experiment_key: string;
  lookback_hours: number;
  strategies: StrategyOutcomeMetricsResponse[];
  generated_at: string;
}

export interface InteractionEventRequest {
  schema_name: "interaction_event.v1";
  event_id: string;
  event_type: InteractionEventType;
  user_id: string;
  content_id: string;
  session_id: string | null;
  topic: string | null;
  watch_duration_seconds: number;
  event_timestamp: string;
  metadata: Record<string, string | number | boolean | null>;
}

export interface InteractionAcceptedResponse {
  event_id: string;
  schema_name: "interaction_event.v1";
  kafka_topic: "interactions.events.v1";
  status: "accepted";
  request_id: string;
  correlation_id: string;
  received_at: string;
  published_at: string | null;
}

export interface ServiceHealthState {
  key: ServiceKey;
  label: string;
  baseUrl: string;
  status: "healthy" | "degraded" | "loading";
  detail: string;
  timestamp: string | null;
}

export interface SessionEventRecord {
  local_id: string;
  event_id: string;
  event_type: InteractionEventType;
  user_id: string;
  content_id: string;
  content_title: string;
  topic: string | null;
  status: "pending" | "accepted" | "failed";
  submitted_at: string;
  received_at: string | null;
  request_id: string | null;
  correlation_id: string | null;
  error_detail: string | null;
}

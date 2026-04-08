import { type CandidateSource, type TopicSlug, TOPIC_ORDER } from "./contracts";

const TOPIC_LABELS: Record<TopicSlug, string> = {
  ai: "AI",
  backend: "Backend",
  "system-design": "System Design",
  devops: "DevOps",
  "interview-prep": "Interview Prep",
};

const CANDIDATE_SOURCE_LABELS: Record<CandidateSource, string> = {
  recent: "Recent",
  trending: "Trending",
  topic_affinity: "Topic Match",
};

const COMPACT_NUMBER_FORMATTER = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 1,
});

const PERCENT_FORMATTER = new Intl.NumberFormat("en-US", {
  style: "percent",
  maximumFractionDigits: 0,
});

const SCORE_FORMATTER = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 3,
  maximumFractionDigits: 3,
});

const DATE_TIME_FORMATTER = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  hour: "numeric",
  minute: "2-digit",
});

export function formatTopicLabel(topic: string): string {
  const normalizedTopic = topic.trim().toLowerCase() as TopicSlug;
  return TOPIC_LABELS[normalizedTopic] ?? startCase(topic);
}

export function formatCandidateSource(source: CandidateSource): string {
  return CANDIDATE_SOURCE_LABELS[source];
}

export function formatPercent(value: number, digits = 0): string {
  return new Intl.NumberFormat("en-US", {
    style: "percent",
    maximumFractionDigits: digits,
  }).format(value);
}

export function formatCompactNumber(value: number): string {
  return COMPACT_NUMBER_FORMATTER.format(value);
}

export function formatScore(value: number): string {
  return SCORE_FORMATTER.format(value);
}

export function formatDateTime(value: string | null): string {
  if (!value) {
    return "Not published";
  }
  return DATE_TIME_FORMATTER.format(new Date(value));
}

export function formatRelativeTime(value: string | null): string {
  if (!value) {
    return "No activity yet";
  }

  const timestamp = new Date(value).getTime();
  const diffInMinutes = Math.round((timestamp - Date.now()) / 60000);
  const formatter = new Intl.RelativeTimeFormat("en", { numeric: "auto" });

  if (Math.abs(diffInMinutes) < 60) {
    return formatter.format(diffInMinutes, "minute");
  }

  const diffInHours = Math.round(diffInMinutes / 60);
  if (Math.abs(diffInHours) < 24) {
    return formatter.format(diffInHours, "hour");
  }

  const diffInDays = Math.round(diffInHours / 24);
  return formatter.format(diffInDays, "day");
}

export function clampToPercent(value: number): number {
  return Math.max(0, Math.min(100, value * 100));
}

export function startCase(value: string): string {
  return value
    .split(/[\s_-]+/)
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

export function sortTopicsByOrder(
  input: Partial<Record<TopicSlug, number>>,
): Array<{ topic: TopicSlug; value: number }> {
  return TOPIC_ORDER.map((topic) => ({
    topic,
    value: input[topic] ?? 0,
  }));
}

export const percentageFormatter = PERCENT_FORMATTER;

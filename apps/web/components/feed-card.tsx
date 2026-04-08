import clsx from "clsx";

import type { FeedItemResponse, InteractionEventType } from "../lib/contracts";
import {
  formatCandidateSource,
  formatCompactNumber,
  formatDateTime,
  formatPercent,
  formatScore,
  formatTopicLabel,
} from "../lib/format";
import { SurfaceCard } from "./surface-card";

type FeedCardProps = {
  item: FeedItemResponse;
  isSelected?: boolean;
  isPending?: boolean;
  actionState?: {
    clicked?: boolean;
    liked?: boolean;
    saved?: boolean;
  };
  variant?: "interactive" | "compact";
  onSelect?: () => void;
  onAction?: (eventType: InteractionEventType) => void;
};

const ACTION_BUTTONS: Array<{
  eventType: InteractionEventType;
  label: string;
  tone: string;
}> = [
  { eventType: "click", label: "Open", tone: "bg-slate-900 text-white" },
  {
    eventType: "like",
    label: "Like",
    tone: "border border-rose-200 bg-rose-50 text-rose-700",
  },
  {
    eventType: "save",
    label: "Save",
    tone: "border border-sky-200 bg-sky-50 text-sky-700",
  },
  {
    eventType: "skip",
    label: "Skip",
    tone: "border border-amber-200 bg-amber-50 text-amber-700",
  },
];

export function FeedCard({
  item,
  isSelected = false,
  isPending = false,
  actionState,
  variant = "interactive",
  onSelect,
  onAction,
}: FeedCardProps) {
  return (
    <SurfaceCard
      className={clsx(
        "transition duration-200",
        isSelected
          ? "border-[color:var(--accent)] shadow-[0_24px_70px_rgba(13,148,136,0.18)]"
          : "hover:-translate-y-0.5 hover:shadow-[0_24px_70px_rgba(15,23,42,0.12)]",
      )}
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-3xl">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--accent)]">
            {formatTopicLabel(item.topic)} / Rank {item.rank}
          </p>
          <button
            type="button"
            onClick={onSelect}
            className="mt-2 text-left font-heading text-3xl leading-tight text-[color:var(--ink-strong)] transition hover:text-[color:var(--accent-strong)]"
          >
            {item.title}
          </button>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-[color:var(--ink-soft)]">
            {item.description ?? "No summary is available for this content item yet."}
          </p>
        </div>

        <div className="min-w-[164px] rounded-[24px] bg-[color:var(--surface-muted)] px-5 py-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[color:var(--ink-soft)]">
            Final score
          </p>
          <p className="mt-2 font-heading text-4xl text-[color:var(--ink-strong)]">
            {formatScore(item.score)}
          </p>
          <p className="mt-2 text-sm text-[color:var(--ink-soft)]">
            {item.candidate_sources.map(formatCandidateSource).join(" · ")}
          </p>
        </div>
      </div>

      <div className="mt-6 flex flex-wrap gap-2">
        {item.candidate_sources.map((source) => (
          <span
            key={`${item.content_id}-${source}`}
            className="rounded-full bg-[color:var(--surface-muted)] px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-[color:var(--ink-soft)]"
          >
            {formatCandidateSource(source)}
          </span>
        ))}
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <MetricPill
          label="Topic affinity"
          value={formatPercent(item.user_topic_affinity)}
          detail={`${formatTopicLabel(item.topic)} fit`}
        />
        <MetricPill
          label="Trending score"
          value={item.content_features.trending_score.toFixed(1)}
          detail={`Updated ${formatDateTime(item.content_features.updated_at)}`}
        />
        <MetricPill
          label="CTR"
          value={formatPercent(item.content_features.ctr)}
          detail={`${formatCompactNumber(item.content_features.impressions)} impressions`}
        />
        <MetricPill
          label="Completion"
          value={formatPercent(item.content_features.completion_rate)}
          detail={`${formatCompactNumber(item.content_features.watch_completes)} completed`}
        />
      </div>

      <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
        <div className="text-sm text-[color:var(--ink-soft)]">
          Published {formatDateTime(item.published_at)}
        </div>
        {variant === "interactive" ? (
          <div className="flex flex-wrap gap-2">
            {ACTION_BUTTONS.map((action) => {
              const isActive =
                (action.eventType === "click" && actionState?.clicked) ||
                (action.eventType === "like" && actionState?.liked) ||
                (action.eventType === "save" && actionState?.saved);
              return (
                <button
                  key={`${item.content_id}-${action.eventType}`}
                  type="button"
                  onClick={() => onAction?.(action.eventType)}
                  disabled={isPending}
                  className={clsx(
                    "rounded-full px-4 py-2 text-sm font-semibold transition",
                    action.tone,
                    isPending && "cursor-wait opacity-60",
                    isActive && "ring-2 ring-offset-2 ring-[color:var(--accent)]",
                  )}
                >
                  {action.label}
                </button>
              );
            })}
            <button
              type="button"
              onClick={onSelect}
              className="rounded-full border border-[color:var(--border-subtle)] bg-white px-4 py-2 text-sm font-semibold text-[color:var(--ink-strong)] transition hover:border-[color:var(--accent)] hover:text-[color:var(--accent-strong)]"
            >
              Explain rank
            </button>
          </div>
        ) : null}
      </div>
    </SurfaceCard>
  );
}

function MetricPill({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <div className="rounded-[24px] bg-[color:var(--surface-muted)] px-4 py-3">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[color:var(--ink-soft)]">
        {label}
      </p>
      <p className="mt-2 text-2xl font-semibold text-[color:var(--ink-strong)]">{value}</p>
      <p className="mt-1 text-sm text-[color:var(--ink-soft)]">{detail}</p>
    </div>
  );
}

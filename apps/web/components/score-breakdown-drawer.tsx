import clsx from "clsx";

import type { FeedItemResponse } from "../lib/contracts";
import {
  clampToPercent,
  formatCompactNumber,
  formatPercent,
  formatScore,
  formatTopicLabel,
} from "../lib/format";

type ScoreBreakdownDrawerProps = {
  item: FeedItemResponse | null;
  isOpen: boolean;
  onClose: () => void;
};

const BREAKDOWN_FIELDS = [
  {
    key: "user_topic_affinity_weighted",
    label: "Topic affinity contribution",
    valueKey: "user_topic_affinity",
  },
  { key: "recency_weighted", label: "Recency contribution", valueKey: "recency" },
  {
    key: "engagement_weighted",
    label: "Engagement contribution",
    valueKey: "engagement",
  },
  { key: "trending_weighted", label: "Trending contribution", valueKey: "trending" },
] as const;

export function ScoreBreakdownDrawer({ item, isOpen, onClose }: ScoreBreakdownDrawerProps) {
  return (
    <>
      <div
        className={clsx(
          "fixed inset-0 z-30 bg-slate-950/30 transition",
          isOpen ? "pointer-events-auto opacity-100" : "pointer-events-none opacity-0",
        )}
        onClick={onClose}
      />
      <aside
        className={clsx(
          "fixed right-0 top-0 z-40 h-full w-full max-w-2xl border-l border-[color:var(--border-subtle)] bg-[color:var(--surface-strong)]/95 p-6 shadow-[0_24px_90px_rgba(15,23,42,0.2)] backdrop-blur-2xl transition-transform duration-300 sm:p-8",
          isOpen ? "translate-x-0" : "translate-x-full",
        )}
      >
        {item ? (
          <div className="flex h-full flex-col">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.28em] text-[color:var(--accent)]">
                  Ranking explanation
                </p>
                <h2 className="mt-3 font-heading text-4xl leading-tight">{item.title}</h2>
                <p className="mt-3 text-sm leading-7 text-[color:var(--ink-soft)]">
                  {item.description ?? "No summary is available for this content item."}
                </p>
              </div>
              <button
                type="button"
                onClick={onClose}
                className="rounded-full border border-[color:var(--border-subtle)] px-3 py-2 text-sm font-semibold text-[color:var(--ink-soft)] transition hover:border-[color:var(--accent)] hover:text-[color:var(--accent-strong)]"
              >
                Close
              </button>
            </div>

            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              <SummaryTile label="Final score" value={formatScore(item.score)} />
              <SummaryTile
                label="Strategy adjustment"
                value={item.score_breakdown.strategy_adjustment.toFixed(3)}
              />
              <SummaryTile
                label="Diversity penalty"
                value={item.score_breakdown.diversity_penalty.toFixed(3)}
              />
              <SummaryTile
                label="Topic"
                value={formatTopicLabel(item.topic)}
                detail={`Affinity ${formatPercent(item.user_topic_affinity)}`}
              />
              <SummaryTile
                label="Trending score"
                value={item.content_features.trending_score.toFixed(1)}
                detail={`${formatCompactNumber(item.content_features.impressions)} impressions`}
              />
            </div>

            <div className="mt-8 space-y-5">
              {BREAKDOWN_FIELDS.map((field) => {
                const weightedValue =
                  item.score_breakdown[field.key as keyof typeof item.score_breakdown];
                const rawValue =
                  item.score_breakdown[field.valueKey as keyof typeof item.score_breakdown];

                return (
                  <div key={field.key}>
                    <div className="flex items-end justify-between gap-4">
                      <div>
                        <p className="text-sm font-semibold text-[color:var(--ink-strong)]">
                          {field.label}
                        </p>
                        <p className="text-sm text-[color:var(--ink-soft)]">
                          Input {formatPercent(Number(rawValue), 1)}
                        </p>
                      </div>
                      <p className="text-sm font-semibold text-[color:var(--ink-strong)]">
                        {Number(weightedValue).toFixed(3)}
                      </p>
                    </div>
                    <div className="mt-3 h-3 overflow-hidden rounded-full bg-[color:var(--surface-muted)]">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-[color:var(--accent)] to-[color:var(--accent-strong)]"
                        style={{ width: `${clampToPercent(Number(weightedValue) / 0.35)}` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="mt-8 grid gap-4 sm:grid-cols-2">
              <SummaryTile
                label="CTR"
                value={formatPercent(item.content_features.ctr)}
                detail={`${formatCompactNumber(item.content_features.clicks)} clicks`}
              />
              <SummaryTile
                label="Like rate"
                value={formatPercent(item.content_features.like_rate)}
                detail={`${formatCompactNumber(item.content_features.likes)} likes`}
              />
              <SummaryTile
                label="Save rate"
                value={formatPercent(item.content_features.save_rate)}
                detail={`${formatCompactNumber(item.content_features.saves)} saves`}
              />
              <SummaryTile
                label="Completion rate"
                value={formatPercent(item.content_features.completion_rate)}
                detail={`${formatCompactNumber(item.content_features.watch_completes)} completions`}
              />
            </div>
          </div>
        ) : null}
      </aside>
    </>
  );
}

function SummaryTile({ label, value, detail }: { label: string; value: string; detail?: string }) {
  return (
    <div className="rounded-[24px] bg-[color:var(--surface-muted)] px-5 py-4">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[color:var(--ink-soft)]">
        {label}
      </p>
      <p className="mt-2 font-heading text-3xl text-[color:var(--ink-strong)]">{value}</p>
      {detail ? <p className="mt-2 text-sm text-[color:var(--ink-soft)]">{detail}</p> : null}
    </div>
  );
}

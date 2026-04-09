import clsx from "clsx";
import { useEffect } from "react";
import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

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

const BREAKDOWN_COLORS = ["#0f766e", "#0369a1", "#ea580c", "#d97706"];
const ENGAGEMENT_COLORS = ["#0f766e", "#0369a1", "#dc2626", "#ea580c", "#7c3aed"];

export function ScoreBreakdownDrawer({ item, isOpen, onClose }: ScoreBreakdownDrawerProps) {
  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  const breakdownData = item
    ? BREAKDOWN_FIELDS.map((field) => ({
        label: field.label.replace(" contribution", ""),
        weighted:
          item.score_breakdown[field.key as keyof typeof item.score_breakdown] as number,
        raw: item.score_breakdown[field.valueKey as keyof typeof item.score_breakdown] as number,
      }))
    : [];

  const engagementMix = item
    ? [
        { label: "CTR", value: Number((item.content_features.ctr * 100).toFixed(1)) },
        { label: "Like", value: Number((item.content_features.like_rate * 100).toFixed(1)) },
        { label: "Save", value: Number((item.content_features.save_rate * 100).toFixed(1)) },
        { label: "Skip", value: Number((item.content_features.skip_rate * 100).toFixed(1)) },
        {
          label: "Complete",
          value: Number((item.content_features.completion_rate * 100).toFixed(1)),
        },
      ]
    : [];

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
          "fixed right-0 top-0 z-40 h-full w-full max-w-2xl overflow-y-auto border-l border-[color:var(--border-subtle)] bg-[color:var(--surface-strong)]/95 p-6 shadow-[0_24px_90px_rgba(15,23,42,0.2)] backdrop-blur-2xl transition-transform duration-300 sm:p-8",
          isOpen ? "translate-x-0" : "translate-x-full",
        )}
        onClick={(event) => event.stopPropagation()}
      >
        {item ? (
          <div className="flex min-h-full flex-col pb-10">
            <div className="sticky top-0 z-10 -mx-6 -mt-6 flex items-start justify-between gap-4 border-b border-[color:var(--border-subtle)] bg-[color:var(--surface-strong)]/95 px-6 py-6 backdrop-blur-2xl sm:-mx-8 sm:px-8">
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

            <div className="mt-8 grid gap-6 xl:grid-cols-[minmax(0,1fr)_260px]">
              <div className="rounded-[26px] bg-[color:var(--surface-muted)] px-4 py-4">
                <p className="text-sm font-semibold text-[color:var(--ink-strong)]">
                  Score composition
                </p>
                <p className="mt-1 text-sm text-[color:var(--ink-soft)]">
                  Weighted components that produced the final deterministic score.
                </p>
                <div className="mt-4 h-[260px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={breakdownData} layout="vertical" margin={{ left: 8, right: 8 }}>
                      <XAxis type="number" tick={{ fill: "var(--ink-soft)", fontSize: 12 }} />
                      <YAxis
                        type="category"
                        dataKey="label"
                        tick={{ fill: "var(--ink-soft)", fontSize: 12 }}
                        width={72}
                      />
                      <Tooltip
                        contentStyle={tooltipStyle}
                        formatter={(value: number, name: string, payload) => {
                          if (name === "weighted") {
                            return [value.toFixed(3), "Weighted contribution"];
                          }
                          return [formatPercent((payload?.payload.raw ?? 0) as number, 1), "Input"];
                        }}
                      />
                      <Bar dataKey="weighted" radius={[0, 12, 12, 0]}>
                        {breakdownData.map((entry, index) => (
                          <Cell
                            key={`${entry.label}-${entry.weighted}`}
                            fill={BREAKDOWN_COLORS[index % BREAKDOWN_COLORS.length]}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="rounded-[26px] bg-[color:var(--surface-muted)] px-4 py-4">
                <p className="text-sm font-semibold text-[color:var(--ink-strong)]">
                  Engagement profile
                </p>
                <p className="mt-1 text-sm text-[color:var(--ink-soft)]">
                  Rate mix from the materialized content feature vector.
                </p>
                <div className="mt-4 h-[220px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={engagementMix}
                        dataKey="value"
                        nameKey="label"
                        innerRadius={52}
                        outerRadius={86}
                        paddingAngle={3}
                      >
                        {engagementMix.map((entry, index) => (
                          <Cell
                            key={`${entry.label}-${entry.value}`}
                            fill={ENGAGEMENT_COLORS[index % ENGAGEMENT_COLORS.length]}
                          />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={tooltipStyle}
                        formatter={(value: number) => [formatPercent(value / 100, 1), "Rate"]}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="mt-3 grid gap-2">
                  {engagementMix.map((entry, index) => (
                    <div
                      key={entry.label}
                      className="flex items-center justify-between rounded-full bg-white/70 px-3 py-2 text-sm"
                    >
                      <span className="flex items-center gap-2 text-[color:var(--ink-soft)]">
                        <span
                          className="block h-2.5 w-2.5 rounded-full"
                          style={{ backgroundColor: ENGAGEMENT_COLORS[index % ENGAGEMENT_COLORS.length] }}
                        />
                        {entry.label}
                      </span>
                      <span className="font-semibold text-[color:var(--ink-strong)]">
                        {formatPercent(entry.value / 100, 1)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
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

const tooltipStyle = {
  borderRadius: "18px",
  border: "1px solid rgba(148, 163, 184, 0.3)",
  background: "rgba(255,255,255,0.96)",
};

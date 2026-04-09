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
  formatCandidateSource,
  formatCompactNumber,
  formatPercent,
  formatScore,
  formatTopicLabel,
} from "../lib/format";
import { SurfaceCard } from "./surface-card";

const CHART_COLORS = ["#0f766e", "#0369a1", "#ea580c", "#d97706", "#be123c"];

type FeedVisualStoryboardProps = {
  items: FeedItemResponse[];
};

export function FeedVisualStoryboard({ items }: FeedVisualStoryboardProps) {
  const topicMix = Object.values(
    items.reduce<
      Record<
        string,
        {
          topic: string;
          value: number;
        }
      >
    >((accumulator, item) => {
      const existing = accumulator[item.topic] ?? {
        topic: formatTopicLabel(item.topic),
        value: 0,
      };
      existing.value += 1;
      accumulator[item.topic] = existing;
      return accumulator;
    }, {}),
  );

  const sourceMix = Object.values(
    items.reduce<
      Record<
        string,
        {
          source: string;
          value: number;
        }
      >
    >((accumulator, item) => {
      for (const source of item.candidate_sources) {
        const existing = accumulator[source] ?? {
          source: formatCandidateSource(source),
          value: 0,
        };
        existing.value += 1;
        accumulator[source] = existing;
      }
      return accumulator;
    }, {}),
  );

  const scoreBands = items.slice(0, 6).map((item) => ({
    title: item.title,
    shortTitle: item.title.length > 20 ? `${item.title.slice(0, 20).trimEnd()}...` : item.title,
    score: Number(item.score.toFixed(3)),
    completionRate: Number((item.content_features.completion_rate * 100).toFixed(1)),
    impressions: item.content_features.impressions,
  }));

  return (
    <SurfaceCard
      title="Feed shape"
      description="A visual read of what the current page is emphasizing across topics, sources, and top-ranked content."
    >
      <div className="grid gap-6 xl:grid-cols-[300px_minmax(0,1fr)_260px]">
        <ChartPanel
          title="Topic mix"
          description="Which topic families dominate the visible ranked page."
        >
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={topicMix}
                  dataKey="value"
                  nameKey="topic"
                  innerRadius={64}
                  outerRadius={96}
                  paddingAngle={4}
                >
                  {topicMix.map((entry, index) => (
                    <Cell
                      key={`${entry.topic}-${entry.value}`}
                      fill={CHART_COLORS[index % CHART_COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={tooltipStyle}
                  formatter={(value: number) => [value, "Items"]}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </ChartPanel>

        <ChartPanel
          title="Ranked content momentum"
          description="Top visible items by final score, with completion rate overlaid for quality context."
        >
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={scoreBands} barGap={10}>
                <XAxis
                  dataKey="shortTitle"
                  tick={{ fill: "var(--ink-soft)", fontSize: 11 }}
                  interval={0}
                  angle={-18}
                  textAnchor="end"
                  height={68}
                />
                <YAxis yAxisId="score" tick={{ fill: "var(--ink-soft)", fontSize: 12 }} />
                <YAxis
                  yAxisId="completion"
                  orientation="right"
                  tick={{ fill: "var(--ink-soft)", fontSize: 12 }}
                />
                <Tooltip
                  contentStyle={tooltipStyle}
                  formatter={(value: number, name: string) => {
                    if (name === "score") {
                      return [formatScore(value), "Final score"];
                    }
                    return [formatPercent(value / 100, 1), "Completion rate"];
                  }}
                />
                <Bar yAxisId="score" dataKey="score" fill="#0f766e" radius={[12, 12, 0, 0]} />
                <Bar
                  yAxisId="completion"
                  dataKey="completionRate"
                  fill="#ea580c"
                  radius={[12, 12, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartPanel>

        <ChartPanel
          title="Retrieval mix"
          description="How many visible items came from recent, trending, or topic-aligned retrieval."
        >
          <div className="space-y-3">
            {sourceMix.map((entry, index) => (
              <div
                key={entry.source}
                className="rounded-[22px] bg-[color:var(--surface-muted)] px-4 py-4"
              >
                <div className="flex items-center justify-between gap-4">
                  <span className="text-sm font-semibold text-[color:var(--ink-strong)]">
                    {entry.source}
                  </span>
                  <span className="text-sm text-[color:var(--ink-soft)]">{entry.value} items</span>
                </div>
                <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/70">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${items.length === 0 ? 0 : (entry.value / items.length) * 100}%`,
                      backgroundColor: CHART_COLORS[index % CHART_COLORS.length],
                    }}
                  />
                </div>
              </div>
            ))}

            {scoreBands[0] ? (
              <div className="rounded-[22px] border border-[color:var(--border-subtle)] bg-white/70 px-4 py-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[color:var(--ink-soft)]">
                  Current hero item
                </p>
                <p className="mt-2 font-heading text-2xl text-[color:var(--ink-strong)]">
                  {scoreBands[0].shortTitle}
                </p>
                <p className="mt-2 text-sm text-[color:var(--ink-soft)]">
                  {formatCompactNumber(scoreBands[0].impressions)} impressions ·{" "}
                  {formatPercent(scoreBands[0].completionRate / 100, 1)} completion
                </p>
              </div>
            ) : null}
          </div>
        </ChartPanel>
      </div>
    </SurfaceCard>
  );
}

function ChartPanel({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-[24px] bg-[color:var(--surface-muted)] px-4 py-4">
      <p className="text-sm font-semibold text-[color:var(--ink-strong)]">{title}</p>
      <p className="mt-1 text-sm text-[color:var(--ink-soft)]">{description}</p>
      <div className="mt-4">{children}</div>
    </div>
  );
}

const tooltipStyle = {
  borderRadius: "18px",
  border: "1px solid rgba(148, 163, 184, 0.3)",
  background: "rgba(255,255,255,0.96)",
};

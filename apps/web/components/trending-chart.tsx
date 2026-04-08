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
import { formatCompactNumber, formatTopicLabel } from "../lib/format";
import { SurfaceCard } from "./surface-card";

const CHART_COLORS = ["#0f766e", "#0369a1", "#c2410c", "#7c3aed", "#be123c"];

type TrendingChartProps = {
  items: FeedItemResponse[];
  categoryDistribution: Array<{ category: string; value: number }>;
};

export function TrendingChart({ items, categoryDistribution }: TrendingChartProps) {
  const barData = items.map((item) => ({
    title: item.title,
    shortTitle: item.title.length > 24 ? `${item.title.slice(0, 24).trimEnd()}...` : item.title,
    trendingScore: Number(item.content_features.trending_score.toFixed(2)),
    impressions: item.content_features.impressions,
    topic: formatTopicLabel(item.topic),
  }));

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
      <SurfaceCard
        title="Trending content"
        description="Highest trending items in the current ranking window, derived from live content features returned by feed-service."
      >
        <div className="h-[320px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={barData}>
              <XAxis
                dataKey="shortTitle"
                tick={{ fill: "var(--ink-soft)", fontSize: 11 }}
                interval={0}
                angle={-18}
                textAnchor="end"
                height={72}
              />
              <YAxis tick={{ fill: "var(--ink-soft)", fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  borderRadius: "18px",
                  border: "1px solid rgba(148, 163, 184, 0.3)",
                  background: "rgba(255,255,255,0.96)",
                }}
                formatter={(value: number, name) =>
                  name === "trendingScore"
                    ? [value.toFixed(2), "Trending score"]
                    : [formatCompactNumber(value), "Impressions"]
                }
              />
              <Bar dataKey="trendingScore" radius={[12, 12, 0, 0]}>
                {barData.map((entry, index) => (
                  <Cell
                    key={`${entry.title}-${entry.topic}`}
                    fill={CHART_COLORS[index % CHART_COLORS.length]}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </SurfaceCard>

      <SurfaceCard
        title="Published catalog mix"
        description="Published content volume by category from content-service."
      >
        <div className="h-[320px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={categoryDistribution}
                dataKey="value"
                nameKey="category"
                innerRadius={72}
                outerRadius={110}
                paddingAngle={3}
              >
                {categoryDistribution.map((entry, index) => (
                  <Cell
                    key={`${entry.category}-${entry.value}`}
                    fill={CHART_COLORS[index % CHART_COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  borderRadius: "18px",
                  border: "1px solid rgba(148, 163, 184, 0.3)",
                  background: "rgba(255,255,255,0.96)",
                }}
                formatter={(value: number) => [value, "Items"]}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-4 grid gap-2">
          {categoryDistribution.map((entry, index) => (
            <div
              key={entry.category}
              className="flex items-center justify-between rounded-full bg-[color:var(--surface-muted)] px-4 py-2 text-sm"
            >
              <span className="flex items-center gap-3 text-[color:var(--ink-soft)]">
                <span
                  className="block h-3 w-3 rounded-full"
                  style={{ backgroundColor: CHART_COLORS[index % CHART_COLORS.length] }}
                />
                {formatTopicLabel(entry.category)}
              </span>
              <span className="font-semibold text-[color:var(--ink-strong)]">{entry.value}</span>
            </div>
          ))}
        </div>
      </SurfaceCard>
    </div>
  );
}

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { StrategyOutcomeMetricsResponse } from "../lib/contracts";
import { formatPercent, startCase } from "../lib/format";
import { SurfaceCard } from "./surface-card";

type ExperimentComparisonChartProps = {
  strategies: StrategyOutcomeMetricsResponse[];
};

export function ExperimentComparisonChart({
  strategies,
}: ExperimentComparisonChartProps) {
  const data = strategies.map((strategy) => ({
    strategy:
      strategy.strategy_name === "rules_v1"
        ? "rules_v1"
        : "rules_v2_with_trending_boost",
    ctr: Number((strategy.ctr * 100).toFixed(1)),
    saveRate: Number((strategy.save_rate * 100).toFixed(1)),
    completionRate: Number((strategy.completion_rate * 100).toFixed(1)),
  }));

  return (
    <SurfaceCard
      title="Strategy outcome comparison"
      description="CTR, save rate, and completion rate are aggregated from attributed item exposures, not from raw request counts."
    >
      <div className="h-[340px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} barGap={10}>
            <CartesianGrid stroke="rgba(100, 116, 139, 0.18)" vertical={false} />
            <XAxis dataKey="strategy" tick={{ fill: "var(--ink-soft)", fontSize: 12 }} />
            <YAxis tick={{ fill: "var(--ink-soft)", fontSize: 12 }} />
            <Tooltip
              contentStyle={{
                borderRadius: "18px",
                border: "1px solid rgba(148, 163, 184, 0.3)",
                background: "rgba(255,255,255,0.96)",
              }}
              formatter={(value: number, name: string) => [
                formatPercent(value / 100, 1),
                startCase(name),
              ]}
            />
            <Bar dataKey="ctr" fill="#0f766e" radius={[12, 12, 0, 0]} />
            <Bar dataKey="saveRate" fill="#0369a1" radius={[12, 12, 0, 0]} />
            <Bar dataKey="completionRate" fill="#c2410c" radius={[12, 12, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </SurfaceCard>
  );
}

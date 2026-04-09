import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import type { SessionEventRecord } from "../lib/contracts";
import { startCase } from "../lib/format";
import { SurfaceCard } from "./surface-card";

const EVENT_COLORS = ["#0f766e", "#0369a1", "#ea580c", "#d97706", "#be123c", "#7c3aed"];

type SessionActivityChartProps = {
  events: SessionEventRecord[];
};

export function SessionActivityChart({ events }: SessionActivityChartProps) {
  const eventMix = Object.values(
    events.reduce<Record<string, { label: string; value: number }>>((accumulator, event) => {
      const existing = accumulator[event.event_type] ?? {
        label: startCase(event.event_type),
        value: 0,
      };
      existing.value += 1;
      accumulator[event.event_type] = existing;
      return accumulator;
    }, {}),
  );

  return (
    <SurfaceCard
      title="Session activity mix"
      description="A visual split of interaction types produced in the current browser session."
    >
      <div className="grid gap-6 lg:grid-cols-[minmax(0,320px)_1fr]">
        <div className="h-[260px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={eventMix}
                dataKey="value"
                nameKey="label"
                innerRadius={62}
                outerRadius={100}
                paddingAngle={4}
              >
                {eventMix.map((entry, index) => (
                  <Cell
                    key={`${entry.label}-${entry.value}`}
                    fill={EVENT_COLORS[index % EVENT_COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip
                contentStyle={tooltipStyle}
                formatter={(value: number) => [value, "Events"]}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="grid gap-3">
          {eventMix.map((entry, index) => (
            <div
              key={entry.label}
              className="flex items-center justify-between rounded-full bg-[color:var(--surface-muted)] px-4 py-3 text-sm"
            >
              <span className="flex items-center gap-3 text-[color:var(--ink-soft)]">
                <span
                  className="block h-3 w-3 rounded-full"
                  style={{ backgroundColor: EVENT_COLORS[index % EVENT_COLORS.length] }}
                />
                {entry.label}
              </span>
              <span className="font-semibold text-[color:var(--ink-strong)]">{entry.value}</span>
            </div>
          ))}

          {eventMix.length === 0 ? (
            <div className="rounded-[24px] bg-[color:var(--surface-muted)] px-4 py-6 text-sm text-[color:var(--ink-soft)]">
              No interaction events have been recorded in this session yet.
            </div>
          ) : null}
        </div>
      </div>
    </SurfaceCard>
  );
}

const tooltipStyle = {
  borderRadius: "18px",
  border: "1px solid rgba(148, 163, 184, 0.3)",
  background: "rgba(255,255,255,0.96)",
};

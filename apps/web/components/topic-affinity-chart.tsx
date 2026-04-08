import { PolarAngleAxis, PolarGrid, Radar, RadarChart, ResponsiveContainer } from "recharts";

import type { TopicSlug } from "../lib/contracts";
import { formatTopicLabel, sortTopicsByOrder } from "../lib/format";
import { SurfaceCard } from "./surface-card";

type TopicAffinityChartProps = {
  title: string;
  description: string;
  profileAffinity: Partial<Record<TopicSlug, number>>;
  observedAffinity?: Partial<Record<TopicSlug, number>>;
};

export function TopicAffinityChart({
  title,
  description,
  profileAffinity,
  observedAffinity,
}: TopicAffinityChartProps) {
  const data = sortTopicsByOrder(profileAffinity).map(({ topic, value }) => ({
    topic: formatTopicLabel(topic),
    profile: Number((value * 100).toFixed(1)),
    observed: Number(((observedAffinity?.[topic] ?? 0) * 100).toFixed(1)),
  }));

  return (
    <SurfaceCard title={title} description={description}>
      <div className="h-[320px]">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={data}>
            <PolarGrid stroke="rgba(100, 116, 139, 0.2)" />
            <PolarAngleAxis dataKey="topic" tick={{ fill: "var(--ink-soft)", fontSize: 12 }} />
            <Radar
              name="Persisted profile"
              dataKey="profile"
              stroke="#0f766e"
              fill="#0f766e"
              fillOpacity={0.2}
              strokeWidth={2}
            />
            <Radar
              name="Live feed signal"
              dataKey="observed"
              stroke="#ea580c"
              fill="#ea580c"
              fillOpacity={0.15}
              strokeWidth={2}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </SurfaceCard>
  );
}

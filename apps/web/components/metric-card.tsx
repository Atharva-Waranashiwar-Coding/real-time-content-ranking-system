import { SurfaceCard } from "./surface-card";

type MetricCardProps = {
  label: string;
  value: string;
  detail: string;
  accent?: "teal" | "orange" | "blue";
};

const accentClassNameMap = {
  teal: "from-teal-500/20 to-teal-100/80 text-teal-800",
  orange: "from-orange-500/20 to-orange-100/80 text-orange-800",
  blue: "from-sky-500/20 to-sky-100/80 text-sky-800",
};

export function MetricCard({ label, value, detail, accent = "teal" }: MetricCardProps) {
  return (
    <SurfaceCard className={`overflow-hidden bg-gradient-to-br ${accentClassNameMap[accent]}`}>
      <p className="text-xs font-semibold uppercase tracking-[0.24em] text-current/80">{label}</p>
      <p className="mt-3 font-heading text-4xl text-[color:var(--ink-strong)]">{value}</p>
      <p className="mt-3 text-sm leading-6 text-[color:var(--ink-soft)]">{detail}</p>
    </SurfaceCard>
  );
}

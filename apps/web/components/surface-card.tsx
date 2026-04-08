import clsx from "clsx";
import type { ReactNode } from "react";

type SurfaceCardProps = {
  title?: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
};

export function SurfaceCard({ title, description, action, children, className }: SurfaceCardProps) {
  return (
    <section
      className={clsx(
        "rounded-[28px] border border-[color:var(--border-subtle)] bg-[color:var(--surface-strong)]/90 p-6 shadow-[0_20px_60px_rgba(15,23,42,0.08)] backdrop-blur",
        className,
      )}
    >
      {(title || description || action) && (
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            {title ? (
              <h2 className="font-heading text-2xl text-[color:var(--ink-strong)]">{title}</h2>
            ) : null}
            {description ? (
              <p className="mt-1 max-w-2xl text-sm text-[color:var(--ink-soft)]">{description}</p>
            ) : null}
          </div>
          {action ? <div className="shrink-0">{action}</div> : null}
        </div>
      )}
      {children}
    </section>
  );
}

import type { SessionEventRecord } from "../lib/contracts";
import { formatDateTime, formatTopicLabel } from "../lib/format";
import { SurfaceCard } from "./surface-card";

type SessionEventStreamProps = {
  events: SessionEventRecord[];
  onClear?: () => void;
};

export function SessionEventStream({ events, onClear }: SessionEventStreamProps) {
  return (
    <SurfaceCard
      title="Session event stream"
      description="Recent interaction events sent from this browser session to interaction-service. This is session-local because the backend does not yet expose a read API for the audit log."
      action={
        onClear ? (
          <button
            type="button"
            onClick={onClear}
            className="rounded-full border border-[color:var(--border-subtle)] px-4 py-2 text-sm font-semibold text-[color:var(--ink-soft)] transition hover:border-[color:var(--accent)] hover:text-[color:var(--accent-strong)]"
          >
            Clear stream
          </button>
        ) : null
      }
    >
      <div className="overflow-x-auto">
        <table className="min-w-full border-separate border-spacing-y-2">
          <thead>
            <tr className="text-left text-xs font-semibold uppercase tracking-[0.18em] text-[color:var(--ink-soft)]">
              <th className="pb-2 pr-4">Event</th>
              <th className="pb-2 pr-4">Content</th>
              <th className="pb-2 pr-4">Status</th>
              <th className="pb-2 pr-4">Trace</th>
              <th className="pb-2">Time</th>
            </tr>
          </thead>
          <tbody>
            {events.map((event) => {
              const statusClassName =
                event.status === "accepted"
                  ? "bg-teal-50 text-teal-800"
                  : event.status === "failed"
                    ? "bg-rose-50 text-rose-800"
                    : "bg-slate-100 text-slate-700";

              return (
                <tr key={event.local_id} className="align-top">
                  <td className="rounded-l-[18px] bg-[color:var(--surface-muted)] px-4 py-3">
                    <p className="font-semibold text-[color:var(--ink-strong)]">
                      {event.event_type}
                    </p>
                    <p className="mt-1 text-xs text-[color:var(--ink-soft)]">
                      {event.topic ? formatTopicLabel(event.topic) : "No topic"}
                    </p>
                  </td>
                  <td className="bg-[color:var(--surface-muted)] px-4 py-3">
                    <p className="max-w-[220px] text-sm text-[color:var(--ink-strong)]">
                      {event.content_title}
                    </p>
                    <p className="mt-1 text-xs text-[color:var(--ink-soft)]">{event.content_id}</p>
                  </td>
                  <td className="bg-[color:var(--surface-muted)] px-4 py-3">
                    <span
                      className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${statusClassName}`}
                    >
                      {event.status}
                    </span>
                    {event.error_detail ? (
                      <p className="mt-2 max-w-[200px] text-xs text-rose-700">
                        {event.error_detail}
                      </p>
                    ) : null}
                  </td>
                  <td className="bg-[color:var(--surface-muted)] px-4 py-3 text-xs text-[color:var(--ink-soft)]">
                    <p>{event.request_id ?? "Request pending"}</p>
                    <p className="mt-1">{event.correlation_id ?? "Correlation pending"}</p>
                  </td>
                  <td className="rounded-r-[18px] bg-[color:var(--surface-muted)] px-4 py-3 text-xs text-[color:var(--ink-soft)]">
                    <p>{formatDateTime(event.submitted_at)}</p>
                    {event.received_at ? (
                      <p className="mt-1">{formatDateTime(event.received_at)}</p>
                    ) : null}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {events.length === 0 ? (
        <p className="mt-4 text-sm text-[color:var(--ink-soft)]">
          No interaction events have been sent from this browser session yet.
        </p>
      ) : null}
    </SurfaceCard>
  );
}

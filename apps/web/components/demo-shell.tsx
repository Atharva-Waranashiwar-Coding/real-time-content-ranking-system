import Link from "next/link";
import { useEffect, useState } from "react";

import { fetchServiceHealth, serviceDefinitions } from "../lib/api";
import type { ServiceHealthState, UserResponse } from "../lib/contracts";
import { formatRelativeTime } from "../lib/format";

type DemoShellProps = {
  activePath: "/" | "/feed" | "/insights" | "/experiments";
  eyebrow: string;
  title: string;
  description: string;
  users: UserResponse[];
  selectedUserId: string | null;
  selectedUser: UserResponse | null;
  onSelectUser: (userId: string) => void;
  children: React.ReactNode;
};

const NAV_ITEMS = [
  { href: "/", label: "Overview" },
  { href: "/feed", label: "Feed" },
  { href: "/insights", label: "Insights" },
  { href: "/experiments", label: "Experiments" },
] as const;

function UserSwitcher({
  users,
  selectedUserId,
  onSelectUser,
}: Pick<DemoShellProps, "users" | "selectedUserId" | "onSelectUser">) {
  return (
    <label className="flex min-w-[220px] flex-col gap-2 text-sm text-[color:var(--ink-soft)]">
      <span className="text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--ink-soft)]/80">
        Demo User
      </span>
      <select
        value={selectedUserId ?? ""}
        onChange={(event) => onSelectUser(event.target.value)}
        className="rounded-2xl border border-[color:var(--border-subtle)] bg-white/80 px-4 py-3 text-base text-[color:var(--ink-strong)] outline-none ring-0 transition focus:border-[color:var(--accent)]"
      >
        {users.length === 0 ? <option value="">Loading users...</option> : null}
        {users.map((user) => (
          <option key={user.id} value={user.id}>
            {user.username}
          </option>
        ))}
      </select>
    </label>
  );
}

function ServiceHealthStrip({ services }: { services: ServiceHealthState[] }) {
  return (
    <div className="mt-8 flex flex-wrap gap-3">
      {services.map((service) => {
        const toneClassName =
          service.status === "healthy"
            ? "border-teal-200 bg-teal-50 text-teal-800"
            : "border-amber-200 bg-amber-50 text-amber-800";

        return (
          <div
            key={service.key}
            className={`rounded-full border px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] ${toneClassName}`}
            title={service.baseUrl}
          >
            {service.label}
            <span className="ml-2 font-normal normal-case tracking-normal">
              {service.status === "healthy"
                ? `healthy ${formatRelativeTime(service.timestamp)}`
                : service.detail}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export function DemoShell({
  activePath,
  eyebrow,
  title,
  description,
  users,
  selectedUserId,
  selectedUser,
  onSelectUser,
  children,
}: DemoShellProps) {
  const [serviceHealth, setServiceHealth] = useState<ServiceHealthState[]>(
    serviceDefinitions.map((service) => ({
      key: service.key,
      label: service.label,
      baseUrl: service.baseUrl,
      status: "loading",
      detail: "Checking service health...",
      timestamp: null,
    })),
  );

  useEffect(() => {
    let isCancelled = false;

    async function loadHealth() {
      const snapshot = await fetchServiceHealth();
      if (!isCancelled) {
        setServiceHealth(snapshot);
      }
    }

    void loadHealth();
    const intervalId = window.setInterval(() => {
      void loadHealth();
    }, 15000);

    return () => {
      isCancelled = true;
      window.clearInterval(intervalId);
    };
  }, []);

  return (
    <div className="min-h-screen bg-[color:var(--bg-app)] text-[color:var(--ink-strong)]">
      <div className="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,rgba(13,148,136,0.12),transparent_30%),radial-gradient(circle_at_top_right,rgba(249,115,22,0.12),transparent_28%),linear-gradient(180deg,#fcfbf7_0%,#f5f1ea_100%)]" />
      <header className="sticky top-0 z-20 border-b border-[color:var(--border-subtle)] bg-[color:var(--surface-glass)]/90 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-4 lg:px-10">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-[color:var(--accent)]">
              Real-Time Ranking Demo
            </p>
            <p className="mt-1 font-heading text-2xl">Tech Learning Feed</p>
          </div>
          <nav className="flex flex-wrap items-center gap-2">
            {NAV_ITEMS.map((item) => {
              const isActive = item.href === activePath;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`rounded-full px-4 py-2 text-sm transition ${
                    isActive
                      ? "bg-[color:var(--ink-strong)] text-white"
                      : "bg-white/50 text-[color:var(--ink-soft)] hover:bg-white"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-10 lg:px-10 lg:py-14">
        <section className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_320px]">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.32em] text-[color:var(--accent)]">
              {eyebrow}
            </p>
            <h1 className="mt-4 max-w-4xl font-heading text-5xl leading-tight lg:text-7xl">
              {title}
            </h1>
            <p className="mt-5 max-w-3xl text-lg leading-8 text-[color:var(--ink-soft)]">
              {description}
            </p>
            <ServiceHealthStrip services={serviceHealth} />
          </div>
          <aside className="rounded-[30px] border border-[color:var(--border-subtle)] bg-[color:var(--surface-strong)]/90 p-6 shadow-[0_20px_60px_rgba(15,23,42,0.08)]">
            <UserSwitcher
              users={users}
              selectedUserId={selectedUserId}
              onSelectUser={onSelectUser}
            />
            {selectedUser ? (
              <div className="mt-6 space-y-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[color:var(--accent-strong)]">
                    Active profile
                  </p>
                  <p className="mt-2 font-heading text-3xl text-[color:var(--ink-strong)]">
                    {selectedUser.username}
                  </p>
                  <p className="mt-1 text-sm text-[color:var(--ink-soft)]">{selectedUser.email}</p>
                </div>
                <p className="text-sm leading-7 text-[color:var(--ink-soft)]">
                  {selectedUser.profile?.bio ?? "No profile bio is available for this user yet."}
                </p>
              </div>
            ) : (
              <p className="mt-6 text-sm text-[color:var(--ink-soft)]">
                Select a user to load the personalized feed and derived insights.
              </p>
            )}
          </aside>
        </section>

        <div className="mt-10">{children}</div>
      </main>
    </div>
  );
}

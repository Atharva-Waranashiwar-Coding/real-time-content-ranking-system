import Head from "next/head";

import { ExperimentComparisonChart } from "../components/experiment-comparison-chart";
import { DemoShell } from "../components/demo-shell";
import { MetricCard } from "../components/metric-card";
import { StateBlock } from "../components/state-block";
import { SurfaceCard } from "../components/surface-card";
import {
  useDemoUsers,
  useExperimentAssignment,
  useExperimentComparison,
} from "../lib/demo-hooks";
import { formatPercent, formatRelativeTime, startCase } from "../lib/format";

function findBestStrategyMetric<
  Key extends "ctr" | "save_rate" | "completion_rate",
>(strategies: Array<Record<Key, number> & { strategy_name: string }>, key: Key) {
  return [...strategies].sort((left, right) => right[key] - left[key])[0] ?? null;
}

const ExperimentsPage = () => {
  const {
    users,
    selectedUserId,
    selectedUser,
    isLoading: isUsersLoading,
    error: usersError,
    setSelectedUserId,
  } = useDemoUsers();
  const {
    assignment,
    isLoading: isAssignmentLoading,
    error: assignmentError,
  } = useExperimentAssignment(selectedUserId);
  const {
    comparison,
    isLoading: isComparisonLoading,
    error: comparisonError,
  } = useExperimentComparison(assignment?.experiment_key ?? null);

  const bestCtr = findBestStrategyMetric(comparison?.strategies ?? [], "ctr");
  const bestCompletion = findBestStrategyMetric(
    comparison?.strategies ?? [],
    "completion_rate",
  );
  const totalExposureRequests = (comparison?.strategies ?? []).reduce(
    (sum, strategy) => sum + strategy.exposure_requests,
    0,
  );

  return (
    <>
      <Head>
        <title>Experiment Dashboard | Real-Time Content Ranking</title>
      </Head>
      <DemoShell
        activePath="/experiments"
        eyebrow="Experimentation"
        title="A live comparison dashboard for ranking strategy outcomes."
        description="This surface shows deterministic user assignment, the active feed ranking experiment, and attributed CTR, save rate, and completion rate by strategy."
        users={users}
        selectedUserId={selectedUserId}
        selectedUser={selectedUser}
        onSelectUser={setSelectedUserId}
      >
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            label="Assigned strategy"
            value={assignment?.strategy_name ?? "Waiting"}
            detail="The selected user's deterministic ranking strategy."
            accent="teal"
          />
          <MetricCard
            label="Assigned variant"
            value={assignment?.variant_key ?? "Waiting"}
            detail="Variant key resolved from the hashed user bucket."
            accent="blue"
          />
          <MetricCard
            label="Best CTR"
            value={bestCtr ? formatPercent(bestCtr.ctr, 1) : "N/A"}
            detail={bestCtr ? `Leader ${bestCtr.strategy_name}` : "No attributed exposures yet."}
            accent="orange"
          />
          <MetricCard
            label="Exposure requests"
            value={String(totalExposureRequests)}
            detail="Delivered feed responses attributed in the comparison window."
            accent="teal"
          />
        </div>

        <div className="mt-8 space-y-8">
          {usersError ? (
            <StateBlock
              title="Demo users are unavailable"
              description={usersError}
              tone="error"
            />
          ) : null}

          {assignmentError ? (
            <StateBlock
              title="Experiment assignment is unavailable"
              description={assignmentError}
              tone="error"
            />
          ) : null}

          {comparisonError ? (
            <StateBlock
              title="Experiment analytics are unavailable"
              description={comparisonError}
              tone="error"
            />
          ) : null}

          {(isUsersLoading || isAssignmentLoading || isComparisonLoading) &&
          !usersError &&
          !assignmentError &&
          !comparisonError ? (
            <StateBlock
              title="Building the experiment dashboard"
              description="Loading the selected user's deterministic assignment and the current comparison metrics from analytics-service."
            />
          ) : null}

          <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_360px]">
            <SurfaceCard
              title="Assignment model"
              description="Users are assigned to a variant by hashing the experiment key and user ID into a stable bucket."
            >
              <div className="grid gap-4 sm:grid-cols-2">
                <AssignmentTile
                  label="Experiment key"
                  value={assignment?.experiment_key ?? "Waiting"}
                />
                <AssignmentTile
                  label="Assignment bucket"
                  value={
                    assignment ? String(assignment.assignment_bucket).padStart(4, "0") : "Waiting"
                  }
                />
                <AssignmentTile
                  label="Assigned at"
                  value={
                    assignment ? formatRelativeTime(assignment.assigned_at) : "Waiting"
                  }
                />
                <AssignmentTile
                  label="Best completion"
                  value={
                    bestCompletion
                      ? `${bestCompletion.strategy_name} · ${formatPercent(
                          bestCompletion.completion_rate,
                          1,
                        )}`
                      : "No comparison data"
                  }
                />
              </div>
            </SurfaceCard>

            <SurfaceCard
              title="Attribution rules"
              description="How experiment outcomes are calculated from exposures and interactions."
            >
              <div className="space-y-4 text-sm leading-7 text-[color:var(--ink-soft)]">
                <p>The denominator is item-level feed exposure rows, not assignment lookups.</p>
                <p>
                  Clicks, saves, and watch completions are attributed to the most recent prior
                  exposure for the same user and content item.
                </p>
                <p>
                  This keeps the comparison tied to the strategy that actually delivered the
                  content, which is what the dashboard is reporting below.
                </p>
              </div>
            </SurfaceCard>
          </div>

          <ExperimentComparisonChart strategies={comparison?.strategies ?? []} />

          <SurfaceCard
            title="Strategy comparison table"
            description="Attributed outcomes by strategy within the configured comparison window."
          >
            <div className="overflow-x-auto">
              <table className="min-w-full border-separate border-spacing-y-2">
                <thead>
                  <tr className="text-left text-xs font-semibold uppercase tracking-[0.18em] text-[color:var(--ink-soft)]">
                    <th className="pb-2 pr-4">Strategy</th>
                    <th className="pb-2 pr-4">Variant</th>
                    <th className="pb-2 pr-4">Exposure Requests</th>
                    <th className="pb-2 pr-4">Item Exposures</th>
                    <th className="pb-2 pr-4">CTR</th>
                    <th className="pb-2 pr-4">Save Rate</th>
                    <th className="pb-2">Completion Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {(comparison?.strategies ?? []).map((strategy) => (
                    <tr key={strategy.strategy_name}>
                      <td className="rounded-l-[18px] bg-[color:var(--surface-muted)] px-4 py-3 text-sm font-semibold text-[color:var(--ink-strong)]">
                        {strategy.strategy_name}
                      </td>
                      <td className="bg-[color:var(--surface-muted)] px-4 py-3 text-sm text-[color:var(--ink-soft)]">
                        {startCase(strategy.variant_key)}
                      </td>
                      <td className="bg-[color:var(--surface-muted)] px-4 py-3 text-sm text-[color:var(--ink-soft)]">
                        {strategy.exposure_requests}
                      </td>
                      <td className="bg-[color:var(--surface-muted)] px-4 py-3 text-sm text-[color:var(--ink-soft)]">
                        {strategy.item_exposures}
                      </td>
                      <td className="bg-[color:var(--surface-muted)] px-4 py-3 text-sm font-semibold text-[color:var(--ink-strong)]">
                        {formatPercent(strategy.ctr, 1)}
                      </td>
                      <td className="bg-[color:var(--surface-muted)] px-4 py-3 text-sm font-semibold text-[color:var(--ink-strong)]">
                        {formatPercent(strategy.save_rate, 1)}
                      </td>
                      <td className="rounded-r-[18px] bg-[color:var(--surface-muted)] px-4 py-3 text-sm font-semibold text-[color:var(--ink-strong)]">
                        {formatPercent(strategy.completion_rate, 1)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {(comparison?.strategies ?? []).length === 0 ? (
              <p className="mt-4 text-sm text-[color:var(--ink-soft)]">
                No experiment exposure data is available yet for the active experiment window.
              </p>
            ) : null}
          </SurfaceCard>
        </div>
      </DemoShell>
    </>
  );
};

function AssignmentTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[24px] bg-[color:var(--surface-muted)] px-4 py-4">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[color:var(--ink-soft)]">
        {label}
      </p>
      <p className="mt-2 text-lg font-semibold text-[color:var(--ink-strong)]">{value}</p>
    </div>
  );
}

export default ExperimentsPage;

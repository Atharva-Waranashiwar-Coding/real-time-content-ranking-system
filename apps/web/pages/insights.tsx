import Head from "next/head";

import { DemoShell } from "../components/demo-shell";
import { MetricCard } from "../components/metric-card";
import { SessionEventStream } from "../components/session-event-stream";
import { StateBlock } from "../components/state-block";
import { SurfaceCard } from "../components/surface-card";
import { TopicAffinityChart } from "../components/topic-affinity-chart";
import { TrendingChart } from "../components/trending-chart";
import { useDemoContext } from "../lib/demo-context";
import { useDemoUsers, useFeedResponse, usePublishedContent } from "../lib/demo-hooks";
import { formatPercent, formatScore, formatTopicLabel } from "../lib/format";
import {
  buildCategoryDistribution,
  buildEventTypeDistribution,
  buildFeedSummary,
  buildObservedAffinity,
  buildTrendingRows,
} from "../lib/insights";

const InsightsPage = () => {
  const {
    users,
    selectedUserId,
    selectedUser,
    isLoading: isUsersLoading,
    error: usersError,
    setSelectedUserId,
  } = useDemoUsers();
  const { recentEvents, clearRecentEvents } = useDemoContext();
  const {
    feed,
    isLoading: isFeedLoading,
    error: feedError,
  } = useFeedResponse({
    userId: selectedUserId,
    limit: 24,
    offset: 0,
  });
  const { catalog, isLoading: isCatalogLoading, error: catalogError } = usePublishedContent(60);

  const profileAffinity = selectedUser?.profile?.topic_preferences ?? {};
  const observedAffinity = buildObservedAffinity(feed?.items ?? []);
  const trendingRows = buildTrendingRows(feed?.items ?? []);
  const categoryDistribution = buildCategoryDistribution(catalog?.items ?? []);
  const feedSummary = buildFeedSummary(feed?.items ?? []);
  const eventTypeDistribution = buildEventTypeDistribution(recentEvents);

  return (
    <>
      <Head>
        <title>Insights Demo | Real-Time Content Ranking</title>
      </Head>
      <DemoShell
        activePath="/insights"
        eyebrow="Ranking insights"
        title="A profile and analytics view that explains why the system is behaving the way it is."
        description="This page combines persisted user preferences, ranked feed outputs, published content catalog data, and the current browser session event stream."
        users={users}
        selectedUserId={selectedUserId}
        selectedUser={selectedUser}
        onSelectUser={setSelectedUserId}
      >
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            label="Live top topic"
            value={feedSummary.leadingTopic ? formatTopicLabel(feedSummary.leadingTopic) : "N/A"}
            detail="Dominant topic in the current ranked candidate set."
            accent="teal"
          />
          <MetricCard
            label="Average score"
            value={formatScore(feedSummary.averageScore)}
            detail="Mean deterministic score across the loaded insights window."
            accent="blue"
          />
          <MetricCard
            label="Average trending"
            value={feedSummary.averageTrending.toFixed(1)}
            detail="Mean content-level trending score from feature-processor."
            accent="orange"
          />
          <MetricCard
            label="Session events"
            value={String(recentEvents.length)}
            detail="Interaction events captured locally in this browser session."
            accent="teal"
          />
        </div>

        <div className="mt-8 space-y-8">
          {usersError ? (
            <StateBlock
              title="User profiles are unavailable"
              description={usersError}
              tone="error"
            />
          ) : null}

          {feedError ? (
            <StateBlock title="Insights feed failed to load" description={feedError} tone="error" />
          ) : null}

          {catalogError ? (
            <StateBlock
              title="Published catalog analytics are unavailable"
              description={catalogError}
              tone="error"
            />
          ) : null}

          {(isUsersLoading || isFeedLoading || isCatalogLoading) && !usersError && !feedError ? (
            <StateBlock
              title="Building insight views"
              description="Loading the selected user profile, ranked feed payload, and published content catalog."
            />
          ) : null}

          <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_360px]">
            <TopicAffinityChart
              title="User topic profile"
              description="The teal shape is persisted user-service preferences. The orange shape reflects the average affinity signal present in the currently ranked feed items."
              profileAffinity={profileAffinity}
              observedAffinity={observedAffinity}
            />

            <SurfaceCard
              title="Signal notes"
              description="A concise explanation of what the current charts are showing."
            >
              <div className="space-y-4 text-sm leading-7 text-[color:var(--ink-soft)]">
                <p>
                  The profile radar is pulled from the selected user&apos;s persisted
                  `topic_preferences`.
                </p>
                <p>
                  The live signal overlay is inferred from ranked feed items, so it shows what the
                  retrieval and ranking stack is currently surfacing.
                </p>
                <p>
                  Event counts below are session-local because interaction-service does not yet
                  expose a read API for the PostgreSQL audit log.
                </p>
              </div>

              <div className="mt-6 grid gap-3">
                {eventTypeDistribution.map((eventBucket) => (
                  <div
                    key={eventBucket.eventType}
                    className="flex items-center justify-between rounded-full bg-[color:var(--surface-muted)] px-4 py-2 text-sm"
                  >
                    <span className="text-[color:var(--ink-soft)]">{eventBucket.eventType}</span>
                    <span className="font-semibold text-[color:var(--ink-strong)]">
                      {eventBucket.value}
                    </span>
                  </div>
                ))}
                {eventTypeDistribution.length === 0 ? (
                  <p className="text-sm text-[color:var(--ink-soft)]">
                    No interaction events have been sent in this browser session yet.
                  </p>
                ) : null}
              </div>
            </SurfaceCard>
          </div>

          <TrendingChart items={trendingRows} categoryDistribution={categoryDistribution} />

          <SurfaceCard
            title="Trending item details"
            description="Top content candidates ordered by live trending score within the current insight window."
          >
            <div className="overflow-x-auto">
              <table className="min-w-full border-separate border-spacing-y-2">
                <thead>
                  <tr className="text-left text-xs font-semibold uppercase tracking-[0.18em] text-[color:var(--ink-soft)]">
                    <th className="pb-2 pr-4">Title</th>
                    <th className="pb-2 pr-4">Topic</th>
                    <th className="pb-2 pr-4">Trending</th>
                    <th className="pb-2 pr-4">Score</th>
                    <th className="pb-2">Completion</th>
                  </tr>
                </thead>
                <tbody>
                  {trendingRows.map((item) => (
                    <tr key={item.content_id}>
                      <td className="rounded-l-[18px] bg-[color:var(--surface-muted)] px-4 py-3 text-sm text-[color:var(--ink-strong)]">
                        {item.title}
                      </td>
                      <td className="bg-[color:var(--surface-muted)] px-4 py-3 text-sm text-[color:var(--ink-soft)]">
                        {formatTopicLabel(item.topic)}
                      </td>
                      <td className="bg-[color:var(--surface-muted)] px-4 py-3 text-sm font-semibold text-[color:var(--ink-strong)]">
                        {item.content_features.trending_score.toFixed(2)}
                      </td>
                      <td className="bg-[color:var(--surface-muted)] px-4 py-3 text-sm font-semibold text-[color:var(--ink-strong)]">
                        {formatScore(item.score)}
                      </td>
                      <td className="rounded-r-[18px] bg-[color:var(--surface-muted)] px-4 py-3 text-sm text-[color:var(--ink-soft)]">
                        {formatPercent(item.content_features.completion_rate)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {trendingRows.length === 0 ? (
              <p className="mt-4 text-sm text-[color:var(--ink-soft)]">
                No ranked items are available to populate the trending table.
              </p>
            ) : null}
          </SurfaceCard>

          <SessionEventStream events={recentEvents} onClear={clearRecentEvents} />
        </div>
      </DemoShell>
    </>
  );
};

export default InsightsPage;

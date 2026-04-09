import Head from "next/head";
import Link from "next/link";

import { DemoShell } from "../components/demo-shell";
import { FeedCard } from "../components/feed-card";
import { MetricCard } from "../components/metric-card";
import { StateBlock } from "../components/state-block";
import { SurfaceCard } from "../components/surface-card";
import { formatPageTitle } from "../lib/branding";
import { TopicAffinityChart } from "../components/topic-affinity-chart";
import { useDemoUsers, useFeedResponse } from "../lib/demo-hooks";
import { formatCompactNumber, formatPercent, formatScore, formatTopicLabel } from "../lib/format";
import { buildFeedSummary, buildObservedAffinity } from "../lib/insights";

const Home = () => {
  const {
    users,
    selectedUserId,
    selectedUser,
    isLoading: isUsersLoading,
    error: usersError,
    setSelectedUserId,
  } = useDemoUsers();
  const {
    feed,
    isLoading: isFeedLoading,
    error: feedError,
  } = useFeedResponse({
    userId: selectedUserId,
    limit: 6,
    offset: 0,
  });

  const feedSummary = buildFeedSummary(feed?.items ?? []);
  const observedAffinity = buildObservedAffinity(feed?.items ?? []);

  return (
    <>
      <Head>
        <title>{formatPageTitle("Overview")}</title>
      </Head>
      <DemoShell
        activePath="/"
        eyebrow="Product overview"
        title="A production-style learning feed, explained in real time."
        description="Atlas Learning turns profile intent, interaction signals, and ranking strategy decisions into a personalized technical learning experience. This interface makes the effects visible instead of hiding them."
        users={users}
        selectedUserId={selectedUserId}
        selectedUser={selectedUser}
        onSelectUser={setSelectedUserId}
      >
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            label="Feed candidates"
            value={String(feed?.total_candidates ?? 0)}
            detail="Candidates retrieved before deterministic ranking and pagination."
            accent="teal"
          />
          <MetricCard
            label="Average score"
            value={formatScore(feedSummary.averageScore)}
            detail="Mean score from ranking-service for the preview window."
            accent="blue"
          />
          <MetricCard
            label="Strongest topic"
            value={feedSummary.leadingTopic ? formatTopicLabel(feedSummary.leadingTopic) : "N/A"}
            detail="Most visible topic in the current personalized payload."
            accent="orange"
          />
          <MetricCard
            label="Preview completion"
            value={formatPercent(feedSummary.averageCompletion)}
            detail="Mean completion rate from live content feature vectors."
            accent="teal"
          />
        </div>

        <div className="mt-8 grid gap-8 xl:grid-cols-[minmax(0,1fr)_420px]">
          <div className="space-y-8">
            {usersError ? (
              <StateBlock title="Unable to load user profiles" description={usersError} tone="error" />
            ) : null}

            {feedError ? (
              <StateBlock
                title="Personalized feed is unavailable"
                description={feedError}
                tone="error"
              />
            ) : null}

            {(isUsersLoading || isFeedLoading) && !usersError && !feedError ? (
              <StateBlock
                title="Loading the product workspace"
                description="Loading the selected profile and a ranked feed preview from feed-service."
              />
            ) : null}

            <SurfaceCard
              title="What powers the feed"
              description="The interface is rendering the same contracts the platform services exchange during real feed generation."
            >
              <div className="grid gap-4 md:grid-cols-3">
                <StoryTile
                  title="Feed-service"
                  description="Retrieves candidates, blends runtime affinity with the user profile, calls ranking-service, then caches the page."
                />
                <StoryTile
                  title="Ranking-service"
                  description="Returns explainable score breakdowns so the UI can show deterministic recency, engagement, trending, and affinity contributions."
                />
                <StoryTile
                  title="Interaction-service"
                  description="Accepts user actions as versioned events for PostgreSQL audit persistence and Kafka fan-out."
                />
              </div>

              <div className="mt-6 flex flex-wrap gap-3">
                <Link
                  href="/feed"
                  className="rounded-full bg-[color:var(--ink-strong)] px-5 py-3 text-sm font-semibold text-white transition hover:opacity-90"
                >
                  Open personalized feed
                </Link>
                <Link
                  href="/insights"
                  className="rounded-full border border-[color:var(--border-subtle)] bg-white px-5 py-3 text-sm font-semibold text-[color:var(--ink-strong)] transition hover:border-[color:var(--accent)] hover:text-[color:var(--accent-strong)]"
                >
                  Explore profile and analytics
                </Link>
                <Link
                  href="/experiments"
                  className="rounded-full border border-[color:var(--border-subtle)] bg-white px-5 py-3 text-sm font-semibold text-[color:var(--ink-strong)] transition hover:border-[color:var(--accent)] hover:text-[color:var(--accent-strong)]"
                >
                  Open experiment dashboard
                </Link>
              </div>
            </SurfaceCard>

            <SurfaceCard
              title="Top-ranked content"
              description="The first few ranked items for the currently selected profile."
            >
              <div className="space-y-5">
                {(feed?.items ?? []).slice(0, 3).map((item) => (
                  <FeedCard key={item.content_id} item={item} variant="compact" />
                ))}
                {feed && feed.items.length === 0 ? (
                  <p className="text-sm text-[color:var(--ink-soft)]">
                    No feed items were returned for this user yet.
                  </p>
                ) : null}
              </div>
            </SurfaceCard>
          </div>

          <div className="space-y-8">
            <TopicAffinityChart
              title="Interest profile"
              description="Persisted topic preferences from user-service against the live signal footprint present in the current ranked payload."
              profileAffinity={selectedUser?.profile?.topic_preferences ?? {}}
              observedAffinity={observedAffinity}
            />

            <SurfaceCard
              title="What ranking changes"
              description="The system is framed as a real product surface, so the feed impact is tied to business and user outcomes instead of only backend mechanics."
            >
              <div className="grid gap-4">
                <StoryTile
                  title="Discovery quality"
                  description="Better candidate selection lifts the chance that a member sees relevant AI, backend, system design, or DevOps content early in the session."
                />
                <StoryTile
                  title="Learning depth"
                  description="Completion rate, saves, and repeat engagement indicate whether the ranking stack is surfacing content worth finishing and returning to."
                />
                <StoryTile
                  title="Product trust"
                  description="Explainable score factors and visible health signals help product, infra, and recruiting audiences understand what the system is doing and why."
                />
              </div>
            </SurfaceCard>

            <SurfaceCard
              title="Preview snapshot"
              description="A quick readout of the currently loaded feed payload."
            >
              <div className="space-y-4">
                <SnapshotRow
                  label="Top item score"
                  value={feed?.items[0] ? formatScore(feed.items[0].score) : "Waiting for data"}
                />
                <SnapshotRow
                  label="Top item impressions"
                  value={
                    feed?.items[0]
                      ? formatCompactNumber(feed.items[0].content_features.impressions)
                      : "Waiting for data"
                  }
                />
                <SnapshotRow
                  label="Top item completion"
                  value={
                    feed?.items[0]
                      ? formatPercent(feed.items[0].content_features.completion_rate)
                      : "Waiting for data"
                  }
                />
              </div>
            </SurfaceCard>
          </div>
        </div>
      </DemoShell>
    </>
  );
};

function StoryTile({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-[24px] bg-[color:var(--surface-muted)] px-4 py-4">
      <p className="font-heading text-2xl text-[color:var(--ink-strong)]">{title}</p>
      <p className="mt-2 text-sm leading-7 text-[color:var(--ink-soft)]">{description}</p>
    </div>
  );
}

function SnapshotRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between rounded-full bg-[color:var(--surface-muted)] px-4 py-3 text-sm">
      <span className="text-[color:var(--ink-soft)]">{label}</span>
      <span className="font-semibold text-[color:var(--ink-strong)]">{value}</span>
    </div>
  );
}

export default Home;

import Head from "next/head";
import { startTransition, useEffect, useMemo, useState } from "react";

import { DemoShell } from "../components/demo-shell";
import { FeedCard } from "../components/feed-card";
import { FeedVisualStoryboard } from "../components/feed-visual-storyboard";
import { MetricCard } from "../components/metric-card";
import { PaginationControls } from "../components/pagination-controls";
import { ScoreBreakdownDrawer } from "../components/score-breakdown-drawer";
import { SessionEventStream } from "../components/session-event-stream";
import { SessionActivityChart } from "../components/session-activity-chart";
import { StateBlock } from "../components/state-block";
import { SurfaceCard } from "../components/surface-card";
import { interactionApi, ApiError } from "../lib/api";
import { formatPageTitle } from "../lib/branding";
import type { FeedItemResponse, InteractionEventType, SessionEventRecord } from "../lib/contracts";
import { useDemoUsers, useFeedResponse } from "../lib/demo-hooks";
import { useDemoContext } from "../lib/demo-context";
import {
  formatCompactNumber,
  formatPercent,
  formatRelativeTime,
  formatScore,
  formatTopicLabel,
} from "../lib/format";
import { buildFeedSummary } from "../lib/insights";
import { buildInteractionRequest, buildPendingSessionEvent } from "../lib/interactions";

const FEED_PAGE_LIMIT = 12;

type ActionState = {
  clicked: boolean;
  liked: boolean;
  saved: boolean;
};

function buildActionState(
  events: SessionEventRecord[],
  userId: string | null,
): Record<string, ActionState> {
  if (!userId) {
    return {};
  }

  return events.reduce<Record<string, ActionState>>((accumulator, event) => {
    if (event.user_id !== userId || event.status !== "accepted") {
      return accumulator;
    }

    const current = accumulator[event.content_id] ?? {
      clicked: false,
      liked: false,
      saved: false,
    };

    if (event.event_type === "click") {
      current.clicked = true;
    }
    if (event.event_type === "like") {
      current.liked = true;
    }
    if (event.event_type === "save") {
      current.saved = true;
    }

    accumulator[event.content_id] = current;
    return accumulator;
  }, {});
}

const FeedPage = () => {
  const {
    users,
    selectedUserId,
    selectedUser,
    isLoading: isUsersLoading,
    error: usersError,
    setSelectedUserId,
  } = useDemoUsers();
  const { sessionId, recentEvents, addRecentEvent, clearRecentEvents, updateRecentEvent } =
    useDemoContext();

  const [offset, setOffset] = useState(0);
  const [selectedContentId, setSelectedContentId] = useState<string | null>(null);
  const [pendingContentIds, setPendingContentIds] = useState<string[]>([]);
  const [dismissedContentIds, setDismissedContentIds] = useState<string[]>([]);

  const {
    feed,
    isLoading: isFeedLoading,
    error: feedError,
  } = useFeedResponse({
    userId: selectedUserId,
    sessionId,
    limit: FEED_PAGE_LIMIT,
    offset,
  });

  useEffect(() => {
    startTransition(() => {
      setOffset(0);
      setDismissedContentIds([]);
    });
  }, [selectedUserId]);

  const visibleItems = useMemo(
    () => (feed?.items ?? []).filter((item) => !dismissedContentIds.includes(item.content_id)),
    [dismissedContentIds, feed?.items],
  );

  useEffect(() => {
    if (visibleItems.length === 0 || !selectedContentId) {
      setSelectedContentId(null);
      return;
    }

    if (!visibleItems.some((item) => item.content_id === selectedContentId)) {
      setSelectedContentId(null);
    }
  }, [selectedContentId, visibleItems]);

  const selectedItem = visibleItems.find((item) => item.content_id === selectedContentId) ?? null;
  const feedSummary = buildFeedSummary(feed?.items ?? []);
  const actionStateByContent = buildActionState(recentEvents, selectedUserId);

  async function handleInteraction(item: FeedItemResponse, eventType: InteractionEventType) {
    if (!selectedUserId) {
      return;
    }

    const payload = buildInteractionRequest({
      eventType,
      item,
      sessionId,
      surface: "web.feed.v1",
      userId: selectedUserId,
      experimentAssignment: feed?.experiment_assignment,
      feedExposureId: feed?.exposure_id,
    });
    const pendingEvent = buildPendingSessionEvent({ payload, item });

    addRecentEvent(pendingEvent);
    setPendingContentIds((previousIds) =>
      previousIds.includes(item.content_id) ? previousIds : [...previousIds, item.content_id],
    );

    try {
      const accepted = await interactionApi.publishEvent(payload);

      updateRecentEvent(pendingEvent.local_id, {
        status: "accepted",
        request_id: accepted.request_id,
        correlation_id: accepted.correlation_id,
        received_at: accepted.received_at,
      });

      if (eventType === "skip") {
        setDismissedContentIds((previousIds) =>
          previousIds.includes(item.content_id) ? previousIds : [...previousIds, item.content_id],
        );
        if (selectedContentId === item.content_id) {
          setSelectedContentId(null);
        }
      }
    } catch (error) {
      updateRecentEvent(pendingEvent.local_id, {
        status: "failed",
        error_detail: error instanceof ApiError ? error.detail : "Interaction request failed.",
      });
    } finally {
      setPendingContentIds((previousIds) =>
        previousIds.filter((contentId) => contentId !== item.content_id),
      );
    }
  }

  return (
    <>
      <Head>
        <title>{formatPageTitle("Feed")}</title>
      </Head>
      <DemoShell
        activePath="/feed"
        eyebrow="Personalized feed"
        title="A feed surface with transparent ranking decisions."
        description="This page shows how profile affinity, recency, engagement, trending behavior, and experimentation shape what a member sees next."
        users={users}
        selectedUserId={selectedUserId}
        selectedUser={selectedUser}
        onSelectUser={setSelectedUserId}
      >
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            label="Candidates"
            value={String(feed?.total_candidates ?? 0)}
            detail="Total retrieved candidates before post-ranking pagination."
            accent="teal"
          />
          <MetricCard
            label="Average score"
            value={formatScore(feedSummary.averageScore)}
            detail="Mean deterministic score for the current page payload."
            accent="blue"
          />
          <MetricCard
            label="Lead topic"
            value={feedSummary.leadingTopic ? formatTopicLabel(feedSummary.leadingTopic) : "N/A"}
            detail="Dominant topic currently visible in the ranked page."
            accent="orange"
          />
          <MetricCard
            label="Completion"
            value={formatPercent(feedSummary.averageCompletion)}
            detail="Average completion rate from feature-processor content vectors."
            accent="teal"
          />
        </div>

        <div className="mt-8 grid gap-8 xl:grid-cols-[minmax(0,1fr)_360px]">
          <div className="space-y-6">
            <FeedVisualStoryboard items={visibleItems} />

            <SurfaceCard
              title="Feed runtime"
              description="Operational details from the live feed response."
            >
              <div className="grid gap-4 sm:grid-cols-3">
                <RuntimeTile
                  label="Cache"
                  value={feed?.cache_hit ? "Hit" : "Miss"}
                  detail="Redis-backed page cache status"
                />
                <RuntimeTile
                  label="Generated"
                  value={feed ? formatRelativeTime(feed.generated_at) : "Waiting"}
                  detail="Timestamp on the latest feed payload"
                />
                <RuntimeTile
                  label="Visible items"
                  value={String(visibleItems.length)}
                  detail={`Page size ${FEED_PAGE_LIMIT}`}
                />
              </div>
              {feed?.experiment_assignment ? (
                <div className="mt-4 grid gap-4 sm:grid-cols-3">
                  <RuntimeTile
                    label="Experiment"
                    value={feed.experiment_assignment.experiment_key}
                    detail="Active experiment used for this feed request"
                  />
                  <RuntimeTile
                    label="Variant"
                    value={feed.experiment_assignment.variant_key}
                    detail={`Strategy ${feed.experiment_assignment.strategy_name}`}
                  />
                  <RuntimeTile
                    label="Exposure"
                    value={feed.exposure_id ?? "Pending"}
                    detail="Exposure row recorded for this delivered feed page"
                  />
                </div>
              ) : null}
            </SurfaceCard>

            {usersError ? (
              <StateBlock
                title="User profiles are unavailable"
                description={usersError}
                tone="error"
              />
            ) : null}

            {!usersError && isUsersLoading ? (
              <StateBlock
                title="Loading user profiles"
                description="Fetching the reference profiles used to drive personalized ranking and retrieval."
              />
            ) : null}

            {!selectedUserId && !isUsersLoading ? (
              <StateBlock
                title="Choose a profile"
                description="The feed cannot be generated until a profile is selected."
              />
            ) : null}

            {selectedUserId && feedError ? (
              <StateBlock title="Feed request failed" description={feedError} tone="error" />
            ) : null}

            {selectedUserId && isFeedLoading ? (
              <StateBlock
                title="Generating personalized feed"
                description="Waiting for candidate retrieval, feature reads, scoring, and cache assembly."
              />
            ) : null}

            {selectedUserId && !isFeedLoading && !feedError && visibleItems.length === 0 ? (
              <StateBlock
                title="No feed items available"
                description="This page is empty after local skips or the backend returned an empty candidate page."
              />
            ) : null}

            {visibleItems.map((item) => (
              <FeedCard
                key={item.content_id}
                item={item}
                isSelected={selectedContentId === item.content_id}
                isPending={pendingContentIds.includes(item.content_id)}
                actionState={actionStateByContent[item.content_id]}
                onSelect={() => setSelectedContentId(item.content_id)}
                onAction={(eventType) => void handleInteraction(item, eventType)}
              />
            ))}

            {feed ? (
              <PaginationControls
                offset={offset}
                limit={FEED_PAGE_LIMIT}
                hasMore={feed.has_more}
                onPrevious={() =>
                  setOffset((currentOffset) => Math.max(0, currentOffset - FEED_PAGE_LIMIT))
                }
                onNext={() => setOffset((currentOffset) => currentOffset + FEED_PAGE_LIMIT)}
              />
            ) : null}
          </div>

          <div className="space-y-6">
            <SurfaceCard
              title="What changes this feed"
              description="The main levers that affect ordering, visibility, and downstream signals."
            >
              <div className="space-y-4 text-sm leading-7 text-[color:var(--ink-soft)]">
                <p>
                  1. Switch profiles to compare how persisted interests reshape candidate retrieval.
                </p>
                <p>
                  2. Open a content card to inspect affinity, recency, engagement, trending, and
                  diversity contributions in the explanation panel.
                </p>
                <p>
                  3. Use like, save, skip, and click actions to generate events that influence the
                  broader ranking system.
                </p>
              </div>
            </SurfaceCard>

            <SessionActivityChart events={recentEvents} />
            <SessionEventStream events={recentEvents} onClear={clearRecentEvents} />
          </div>
        </div>

        <ScoreBreakdownDrawer
          item={selectedItem}
          isOpen={Boolean(selectedContentId && selectedItem)}
          onClose={() => setSelectedContentId(null)}
        />
      </DemoShell>
    </>
  );
};

function RuntimeTile({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <div className="rounded-[24px] bg-[color:var(--surface-muted)] px-4 py-4">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[color:var(--ink-soft)]">
        {label}
      </p>
      <p className="mt-2 text-2xl font-semibold text-[color:var(--ink-strong)]">{value}</p>
      <p className="mt-1 text-sm text-[color:var(--ink-soft)]">{detail}</p>
    </div>
  );
}

export default FeedPage;

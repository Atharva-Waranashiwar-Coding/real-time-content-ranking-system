import type {
  ContentItemResponse,
  FeedItemResponse,
  SessionEventRecord,
  TopicSlug,
} from "./contracts";
import { TOPIC_ORDER } from "./contracts";

export function buildObservedAffinity(feedItems: FeedItemResponse[]) {
  return TOPIC_ORDER.reduce<Partial<Record<TopicSlug, number>>>((accumulator, topic) => {
    const topicItems = feedItems.filter((item) => item.topic === topic);
    if (topicItems.length === 0) {
      accumulator[topic] = 0;
      return accumulator;
    }

    const averageAffinity =
      topicItems.reduce((sum, item) => sum + item.user_topic_affinity, 0) / topicItems.length;

    accumulator[topic] = averageAffinity;
    return accumulator;
  }, {});
}

export function buildTrendingRows(feedItems: FeedItemResponse[]) {
  return [...feedItems]
    .sort(
      (left, right) => right.content_features.trending_score - left.content_features.trending_score,
    )
    .slice(0, 8);
}

export function buildCategoryDistribution(items: Array<Pick<ContentItemResponse, "category">>) {
  const counts = items.reduce<Record<string, number>>((accumulator, item) => {
    accumulator[item.category] = (accumulator[item.category] ?? 0) + 1;
    return accumulator;
  }, {});

  return Object.entries(counts).map(([category, value]) => ({
    category,
    value,
  }));
}

export function buildFeedSummary(feedItems: FeedItemResponse[]) {
  const totalItems = feedItems.length;
  const aggregateScore = feedItems.reduce((sum, item) => sum + item.score, 0);
  const aggregateTrending = feedItems.reduce(
    (sum, item) => sum + item.content_features.trending_score,
    0,
  );
  const aggregateCompletion = feedItems.reduce(
    (sum, item) => sum + item.content_features.completion_rate,
    0,
  );

  const leadingTopic = TOPIC_ORDER.map((topic) => ({
    topic,
    count: feedItems.filter((item) => item.topic === topic).length,
  })).sort((left, right) => right.count - left.count)[0];

  return {
    totalItems,
    averageScore: totalItems > 0 ? aggregateScore / totalItems : 0,
    averageTrending: totalItems > 0 ? aggregateTrending / totalItems : 0,
    averageCompletion: totalItems > 0 ? aggregateCompletion / totalItems : 0,
    leadingTopic: leadingTopic?.count ? leadingTopic.topic : null,
  };
}

export function buildEventTypeDistribution(recentEvents: SessionEventRecord[]) {
  const counts = recentEvents.reduce<Record<string, number>>((accumulator, event) => {
    accumulator[event.event_type] = (accumulator[event.event_type] ?? 0) + 1;
    return accumulator;
  }, {});

  return Object.entries(counts).map(([eventType, value]) => ({
    eventType,
    value,
  }));
}

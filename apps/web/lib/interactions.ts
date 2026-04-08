import type {
  ExperimentAssignmentResponse,
  FeedItemResponse,
  InteractionEventRequest,
  InteractionEventType,
  SessionEventRecord,
} from "./contracts";

function createUuid(): string {
  if (typeof globalThis.crypto?.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }

  const chunk = () =>
    Math.floor(Math.random() * 0xffffffff)
      .toString(16)
      .padStart(8, "0");
  const head = `${chunk()}-${chunk().slice(0, 4)}-4${chunk().slice(0, 3)}`;
  const tail = `a${chunk().slice(0, 3)}-${chunk()}${chunk().slice(0, 4)}`;
  return `${head}-${tail}`;
}

export function buildInteractionRequest({
  eventType,
  userId,
  sessionId,
  item,
  surface,
  experimentAssignment,
  feedExposureId,
}: {
  eventType: InteractionEventType;
  userId: string;
  sessionId: string;
  item: FeedItemResponse;
  surface: string;
  experimentAssignment?: ExperimentAssignmentResponse | null;
  feedExposureId?: string | null;
}): InteractionEventRequest {
  return {
    schema_name: "interaction_event.v1",
    event_id: createUuid(),
    event_type: eventType,
    user_id: userId,
    content_id: item.content_id,
    session_id: sessionId,
    topic: item.topic,
    watch_duration_seconds: 0,
    event_timestamp: new Date().toISOString(),
    metadata: {
      surface,
      rank: item.rank,
      category: item.category,
      score: Number(item.score.toFixed(6)),
      experiment_key: experimentAssignment?.experiment_key ?? null,
      variant_key: experimentAssignment?.variant_key ?? null,
      strategy_name: experimentAssignment?.strategy_name ?? null,
      feed_exposure_id: feedExposureId ?? null,
    },
  };
}

export function buildPendingSessionEvent({
  payload,
  item,
}: {
  payload: InteractionEventRequest;
  item: FeedItemResponse;
}): SessionEventRecord {
  return {
    local_id: `local-${payload.event_id}`,
    event_id: payload.event_id,
    event_type: payload.event_type,
    user_id: payload.user_id,
    content_id: payload.content_id,
    content_title: item.title,
    topic: item.topic,
    status: "pending",
    submitted_at: payload.event_timestamp,
    received_at: null,
    request_id: null,
    correlation_id: null,
    error_detail: null,
  };
}

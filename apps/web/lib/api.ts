import type {
  ContentListResponse,
  ExperimentAssignmentResponse,
  ExperimentComparisonResponse,
  FeedResponse,
  HealthCheckResponse,
  InteractionAcceptedResponse,
  InteractionEventRequest,
  ServiceHealthState,
  ServiceKey,
  UserResponse,
} from "./contracts";

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
};

type ServiceDefinition = {
  key: ServiceKey;
  label: string;
  baseUrl: string;
};

const DEFAULT_SERVICE_URLS = {
  feed: process.env.NEXT_PUBLIC_FEED_SERVICE_URL ?? "http://localhost:8004",
  user: process.env.NEXT_PUBLIC_USER_SERVICE_URL ?? "http://localhost:8001",
  content: process.env.NEXT_PUBLIC_CONTENT_SERVICE_URL ?? "http://localhost:8002",
  interaction: process.env.NEXT_PUBLIC_INTERACTION_SERVICE_URL ?? "http://localhost:8003",
  experimentation:
    process.env.NEXT_PUBLIC_EXPERIMENTATION_SERVICE_URL ?? "http://localhost:8006",
  analytics: process.env.NEXT_PUBLIC_ANALYTICS_SERVICE_URL ?? "http://localhost:8007",
};

export const serviceDefinitions: ServiceDefinition[] = [
  { key: "feed", label: "Feed", baseUrl: DEFAULT_SERVICE_URLS.feed },
  { key: "user", label: "User", baseUrl: DEFAULT_SERVICE_URLS.user },
  { key: "content", label: "Content", baseUrl: DEFAULT_SERVICE_URLS.content },
  {
    key: "interaction",
    label: "Interaction",
    baseUrl: DEFAULT_SERVICE_URLS.interaction,
  },
  {
    key: "experimentation",
    label: "Experimentation",
    baseUrl: DEFAULT_SERVICE_URLS.experimentation,
  },
  {
    key: "analytics",
    label: "Analytics",
    baseUrl: DEFAULT_SERVICE_URLS.analytics,
  },
];

export class ApiError extends Error {
  status: number;
  service: ServiceKey;
  detail: string;

  constructor({
    service,
    status,
    detail,
  }: {
    service: ServiceKey;
    status: number;
    detail: string;
  }) {
    super(detail);
    this.name = "ApiError";
    this.service = service;
    this.status = status;
    this.detail = detail;
  }
}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const payload = await response.json();
    if (typeof payload?.detail === "string") {
      return payload.detail;
    }
  } catch {
    return `HTTP ${response.status}`;
  }

  return `HTTP ${response.status}`;
}

function buildTraceId(prefix: "req" | "corr"): string {
  if (typeof globalThis.crypto?.randomUUID === "function") {
    return `${prefix}-${globalThis.crypto.randomUUID()}`;
  }

  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

async function requestJson<T>(
  service: ServiceKey,
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const baseUrl = DEFAULT_SERVICE_URLS[service];
  const { body, ...requestOptions } = options;
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  headers.set("X-Request-ID", buildTraceId("req"));
  headers.set("X-Correlation-ID", buildTraceId("corr"));

  const init: RequestInit = {
    ...requestOptions,
    headers,
  };

  if (body !== undefined) {
    headers.set("Content-Type", "application/json");
    init.body = JSON.stringify(body);
  }

  const response = await fetch(`${baseUrl}${path}`, init);
  if (!response.ok) {
    throw new ApiError({
      service,
      status: response.status,
      detail: await parseErrorDetail(response),
    });
  }

  return (await response.json()) as T;
}

export const userApi = {
  listUsers(limit = 100): Promise<UserResponse[]> {
    return requestJson<UserResponse[]>("user", `/api/v1/users?skip=0&limit=${limit}`);
  },
};

export const feedApi = {
  getFeed({
    userId,
    sessionId,
    limit,
    offset,
  }: {
    userId: string;
    sessionId?: string;
    limit: number;
    offset: number;
  }): Promise<FeedResponse> {
    const params = new URLSearchParams({
      user_id: userId,
      limit: String(limit),
      offset: String(offset),
    });
    if (sessionId) {
      params.set("session_id", sessionId);
    }
    return requestJson<FeedResponse>("feed", `/api/v1/feed?${params.toString()}`);
  },
};

export const contentApi = {
  listPublishedContent(limit = 100): Promise<ContentListResponse> {
    return requestJson<ContentListResponse>(
      "content",
      `/api/v1/content?status=published&skip=0&limit=${limit}`,
    );
  },
};

export const interactionApi = {
  publishEvent(payload: InteractionEventRequest): Promise<InteractionAcceptedResponse> {
    return requestJson<InteractionAcceptedResponse>("interaction", "/api/v1/interactions", {
      method: "POST",
      body: payload,
    });
  },
};

export const experimentationApi = {
  getAssignment(userId: string): Promise<ExperimentAssignmentResponse> {
    return requestJson<ExperimentAssignmentResponse>(
      "experimentation",
      `/api/v1/experiments/assignment?user_id=${userId}`,
    );
  },
};

export const analyticsApi = {
  getExperimentComparison({
    experimentKey,
    lookbackHours = 168,
  }: {
    experimentKey: string;
    lookbackHours?: number;
  }): Promise<ExperimentComparisonResponse> {
    return requestJson<ExperimentComparisonResponse>(
      "analytics",
      `/api/v1/experiments/${experimentKey}/comparison?lookback_hours=${lookbackHours}`,
    );
  },
};

async function fetchHealthState(definition: ServiceDefinition): Promise<ServiceHealthState> {
  try {
    const payload = await requestJson<HealthCheckResponse>(definition.key, "/api/v1/health");
    return {
      key: definition.key,
      label: definition.label,
      baseUrl: definition.baseUrl,
      status: payload.status === "healthy" ? "healthy" : "degraded",
      detail: payload.service,
      timestamp: payload.timestamp,
    };
  } catch (error) {
    const detail = error instanceof ApiError ? error.detail : "Health endpoint unreachable";
    return {
      key: definition.key,
      label: definition.label,
      baseUrl: definition.baseUrl,
      status: "degraded",
      detail,
      timestamp: null,
    };
  }
}

export async function fetchServiceHealth(): Promise<ServiceHealthState[]> {
  return Promise.all(serviceDefinitions.map(fetchHealthState));
}

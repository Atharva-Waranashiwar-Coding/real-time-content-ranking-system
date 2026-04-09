import { startTransition, useEffect, useMemo, useState } from "react";

import {
  analyticsApi,
  ApiError,
  contentApi,
  experimentationApi,
  feedApi,
  userApi,
} from "./api";
import type {
  ContentListResponse,
  ExperimentAssignmentResponse,
  ExperimentComparisonResponse,
  FeedResponse,
  UserResponse,
} from "./contracts";
import { useDemoContext } from "./demo-context";

const DEMO_USER_ORDER: string[] = [
  "alice_dev",
  "bob_engineer",
  "charlie_sysadmin",
  "dana_ml",
  "emma_fullstack",
];

function sortDemoUsers(users: UserResponse[]): UserResponse[] {
  const positionByUsername = new Map(
    DEMO_USER_ORDER.map((username, index) => [username, index]),
  );

  return [...users].sort((left, right) => {
    const leftPosition = positionByUsername.get(left.username) ?? Number.MAX_SAFE_INTEGER;
    const rightPosition = positionByUsername.get(right.username) ?? Number.MAX_SAFE_INTEGER;
    if (leftPosition !== rightPosition) {
      return leftPosition - rightPosition;
    }
    return left.username.localeCompare(right.username);
  });
}

export function useDemoUsers() {
  const { isHydrated, selectedUserId, setSelectedUserId } = useDemoContext();
  const [users, setUsers] = useState<UserResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isHydrated) {
      return;
    }

    let isCancelled = false;

    async function loadUsers() {
      setIsLoading(true);
      setError(null);

      try {
        const response = await userApi.listUsers();
        if (isCancelled) {
          return;
        }

        const sortedUsers = sortDemoUsers(response);
        setUsers(sortedUsers);

        if (!selectedUserId && sortedUsers.length > 0) {
          startTransition(() => {
            setSelectedUserId(sortedUsers[0].id);
          });
        }

        if (
          selectedUserId &&
          sortedUsers.length > 0 &&
          !sortedUsers.some((user) => user.id === selectedUserId)
        ) {
          startTransition(() => {
            setSelectedUserId(sortedUsers[0].id);
          });
        }
      } catch (error) {
        if (!isCancelled) {
          setError(error instanceof ApiError ? error.detail : "Unable to load user profiles.");
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadUsers();

    return () => {
      isCancelled = true;
    };
  }, [isHydrated, selectedUserId, setSelectedUserId]);

  const selectedUser = useMemo(
    () => users.find((user) => user.id === selectedUserId) ?? null,
    [selectedUserId, users],
  );

  return {
    users,
    selectedUserId,
    selectedUser,
    isLoading,
    error,
    setSelectedUserId,
  };
}

export function useFeedResponse({
  userId,
  sessionId,
  limit,
  offset,
}: {
  userId: string | null;
  sessionId?: string;
  limit: number;
  offset: number;
}) {
  const [feed, setFeed] = useState<FeedResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!userId) {
      setFeed(null);
      setIsLoading(false);
      return;
    }

    let isCancelled = false;
    const resolvedUserId = userId;

    async function loadFeed() {
      setIsLoading(true);
      setError(null);

      try {
        const response = await feedApi.getFeed({
          userId: resolvedUserId,
          sessionId,
          limit,
          offset,
        });
        if (!isCancelled) {
          setFeed(response);
        }
      } catch (error) {
        if (!isCancelled) {
          setError(
            error instanceof ApiError ? error.detail : "Unable to load the personalized feed.",
          );
          setFeed(null);
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadFeed();

    return () => {
      isCancelled = true;
    };
  }, [limit, offset, sessionId, userId]);

  return { feed, isLoading, error };
}

export function usePublishedContent(limit: number) {
  const [catalog, setCatalog] = useState<ContentListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isCancelled = false;

    async function loadCatalog() {
      setIsLoading(true);
      setError(null);

      try {
        const response = await contentApi.listPublishedContent(limit);
        if (!isCancelled) {
          setCatalog(response);
        }
      } catch (error) {
        if (!isCancelled) {
          setError(
            error instanceof ApiError
              ? error.detail
              : "Unable to load the published content catalog.",
          );
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadCatalog();

    return () => {
      isCancelled = true;
    };
  }, [limit]);

  return { catalog, isLoading, error };
}

export function useExperimentAssignment(userId: string | null) {
  const [assignment, setAssignment] = useState<ExperimentAssignmentResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!userId) {
      setAssignment(null);
      setIsLoading(false);
      return;
    }

    let isCancelled = false;
    const resolvedUserId = userId;

    async function loadAssignment() {
      setIsLoading(true);
      setError(null);

      try {
        const response = await experimentationApi.getAssignment(resolvedUserId);
        if (!isCancelled) {
          setAssignment(response);
        }
      } catch (error) {
        if (!isCancelled) {
          setError(
            error instanceof ApiError
              ? error.detail
              : "Unable to load the experiment assignment.",
          );
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadAssignment();

    return () => {
      isCancelled = true;
    };
  }, [userId]);

  return { assignment, isLoading, error };
}

export function useExperimentComparison(
  experimentKey: string | null,
  lookbackHours = 168,
) {
  const [comparison, setComparison] = useState<ExperimentComparisonResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!experimentKey) {
      setComparison(null);
      setIsLoading(false);
      return;
    }

    let isCancelled = false;
    const resolvedExperimentKey = experimentKey;

    async function loadComparison() {
      setIsLoading(true);
      setError(null);

      try {
        const response = await analyticsApi.getExperimentComparison({
          experimentKey: resolvedExperimentKey,
          lookbackHours,
        });
        if (!isCancelled) {
          setComparison(response);
        }
      } catch (error) {
        if (!isCancelled) {
          setError(
            error instanceof ApiError
              ? error.detail
              : "Unable to load the experiment comparison.",
          );
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadComparison();

    return () => {
      isCancelled = true;
    };
  }, [experimentKey, lookbackHours]);

  return { comparison, isLoading, error };
}

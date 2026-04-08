"use client";

import { createContext, type ReactNode, useContext, useEffect, useMemo, useState } from "react";

import type { SessionEventRecord } from "./contracts";

type DemoContextValue = {
  isHydrated: boolean;
  selectedUserId: string | null;
  sessionId: string;
  recentEvents: SessionEventRecord[];
  setSelectedUserId: (userId: string) => void;
  addRecentEvent: (event: SessionEventRecord) => void;
  updateRecentEvent: (localId: string, update: Partial<SessionEventRecord>) => void;
  clearRecentEvents: () => void;
};

const DEFAULT_STORAGE_KEYS = {
  sessionId: "demo-session-id",
  selectedUserId: "demo-selected-user-id",
  recentEvents: "demo-session-events",
};

const DEFAULT_SESSION_EVENT_LIMIT = 24;
const DemoContext = createContext<DemoContextValue | null>(null);

function createSessionId(): string {
  if (typeof globalThis.crypto?.randomUUID === "function") {
    return `web-session-${globalThis.crypto.randomUUID()}`;
  }
  return `web-session-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

export function DemoProvider({ children }: { children: ReactNode }) {
  const [isHydrated, setIsHydrated] = useState(false);
  const [selectedUserId, setSelectedUserIdState] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState("web-session-pending");
  const [recentEvents, setRecentEvents] = useState<SessionEventRecord[]>([]);

  useEffect(() => {
    const storedSessionId =
      window.localStorage.getItem(DEFAULT_STORAGE_KEYS.sessionId) ?? createSessionId();
    const storedSelectedUserId = window.localStorage.getItem(DEFAULT_STORAGE_KEYS.selectedUserId);
    const storedRecentEvents = window.localStorage.getItem(DEFAULT_STORAGE_KEYS.recentEvents);

    window.localStorage.setItem(DEFAULT_STORAGE_KEYS.sessionId, storedSessionId);
    setSessionId(storedSessionId);
    setSelectedUserIdState(storedSelectedUserId);

    if (storedRecentEvents) {
      try {
        const parsedEvents = JSON.parse(storedRecentEvents) as SessionEventRecord[];
        setRecentEvents(parsedEvents);
      } catch {
        window.localStorage.removeItem(DEFAULT_STORAGE_KEYS.recentEvents);
      }
    }

    setIsHydrated(true);
  }, []);

  useEffect(() => {
    if (!isHydrated) {
      return;
    }

    if (selectedUserId) {
      window.localStorage.setItem(DEFAULT_STORAGE_KEYS.selectedUserId, selectedUserId);
    } else {
      window.localStorage.removeItem(DEFAULT_STORAGE_KEYS.selectedUserId);
    }
  }, [isHydrated, selectedUserId]);

  useEffect(() => {
    if (!isHydrated) {
      return;
    }

    window.localStorage.setItem(DEFAULT_STORAGE_KEYS.recentEvents, JSON.stringify(recentEvents));
  }, [isHydrated, recentEvents]);

  const value = useMemo<DemoContextValue>(
    () => ({
      isHydrated,
      selectedUserId,
      sessionId,
      recentEvents,
      setSelectedUserId: (userId: string) => setSelectedUserIdState(userId),
      addRecentEvent: (event: SessionEventRecord) => {
        setRecentEvents((previousEvents) =>
          [event, ...previousEvents].slice(0, DEFAULT_SESSION_EVENT_LIMIT),
        );
      },
      updateRecentEvent: (localId: string, update: Partial<SessionEventRecord>) => {
        setRecentEvents((previousEvents) =>
          previousEvents.map((event) =>
            event.local_id === localId ? { ...event, ...update } : event,
          ),
        );
      },
      clearRecentEvents: () => setRecentEvents([]),
    }),
    [isHydrated, recentEvents, selectedUserId, sessionId],
  );

  return <DemoContext.Provider value={value}>{children}</DemoContext.Provider>;
}

export function useDemoContext(): DemoContextValue {
  const context = useContext(DemoContext);
  if (!context) {
    throw new Error("useDemoContext must be used within DemoProvider");
  }
  return context;
}

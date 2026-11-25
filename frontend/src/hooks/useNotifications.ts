"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import useToast from "@/hooks/useToast";
import { apiClient } from "@/lib/apiClient";
import { getErrorMessage } from "@/lib/errorHandler";
import type { Notification } from "@/types/api";

const POLL_INTERVAL_MS = 30_000;

interface UseNotificationsResult {
  items: Notification[];
  unreadCount: number;
  isUnreadOnly: boolean;
  isLoading: boolean;
  isLoadingMore: boolean;
  hasMore: boolean;
  error: string | null;
  setUnreadOnly: (isUnreadOnly: boolean) => void;
  loadMore: () => Promise<void>;
  markRead: (notificationId: string) => Promise<void>;
  retry: () => void;
}

export default function useNotifications(): UseNotificationsResult {
  const { showError } = useToast();
  // Polling retries every 30 s; toast once per outage, not on every retry.
  const hasPollFailedRef = useRef<boolean>(false);
  const [isUnreadOnly, setIsUnreadOnly] = useState<boolean>(false);
  // The newest page, replaced on every poll (requested without a cursor).
  const [newest, setNewest] = useState<Notification[]>([]);
  const [newestCursor, setNewestCursor] = useState<string | null>(null);
  // Older pages, loaded on demand through nextCursor.
  const [older, setOlder] = useState<Notification[]>([]);
  const [olderCursor, setOlderCursor] = useState<string | null>(null);
  const [hasLoadedOlder, setHasLoadedOlder] = useState<boolean>(false);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isLoadingMore, setIsLoadingMore] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState<number>(0);

  // Poll the newest page and reset older pages when the filter changes.
  useEffect(() => {
    let isActive = true;
    const poll = async (): Promise<void> => {
      try {
        const [page, unread] = await Promise.all([
          apiClient.listNotifications({ unreadOnly: isUnreadOnly || undefined }),
          isUnreadOnly
            ? Promise.resolve(null)
            : apiClient.listNotifications({ unreadOnly: true }),
        ]);
        if (!isActive) return;
        setNewest(page.items);
        setNewestCursor(page.nextCursor);
        const unreadItems = unread ? unread.items : page.items;
        setUnreadCount(unreadItems.filter((n) => n.status === "unread").length);
        setError(null);
        hasPollFailedRef.current = false;
      } catch (err: unknown) {
        if (!isActive) return;
        setError(getErrorMessage(err, "Could not load notifications."));
        if (!hasPollFailedRef.current) {
          showError(err, "Could not load notifications.");
        }
        hasPollFailedRef.current = true;
      } finally {
        if (isActive) setIsLoading(false);
      }
    };

    void poll();
    const timer = setInterval(() => void poll(), POLL_INTERVAL_MS);
    return () => {
      isActive = false;
      clearInterval(timer);
    };
  }, [isUnreadOnly, reloadKey, showError]);

  const loadMore = useCallback(async () => {
    const cursor = hasLoadedOlder ? olderCursor : newestCursor;
    if (!cursor) return;
    setIsLoadingMore(true);
    try {
      const page = await apiClient.listNotifications({
        cursor,
        unreadOnly: isUnreadOnly || undefined,
      });
      setOlder((prev) => [...prev, ...page.items]);
      setOlderCursor(page.nextCursor);
      setHasLoadedOlder(true);
    } catch (err: unknown) {
      showError(err, "Could not load older notifications.");
    } finally {
      setIsLoadingMore(false);
    }
  }, [hasLoadedOlder, olderCursor, newestCursor, isUnreadOnly, showError]);

  const markRead = useCallback(
    async (notificationId: string) => {
      try {
        const updated = await apiClient.markNotificationRead(notificationId);
        const apply = (list: Notification[]): Notification[] =>
          list.map((n) => (n.id === updated.id ? updated : n));
        setNewest(apply);
        setOlder(apply);
        setUnreadCount((count) => Math.max(0, count - 1));
      } catch (err: unknown) {
        showError(err, "Could not mark the notification as read.");
      }
    },
    [showError],
  );

  const items = useMemo(() => {
    const seen = new Set<string>();
    return [...newest, ...older].filter((n) => {
      if (seen.has(n.id)) return false;
      seen.add(n.id);
      return true;
    });
  }, [newest, older]);

  const hasMore = hasLoadedOlder ? olderCursor !== null : newestCursor !== null;

  const setUnreadOnly = useCallback((value: boolean) => {
    setIsLoading(true);
    setOlder([]);
    setOlderCursor(null);
    setHasLoadedOlder(false);
    setIsUnreadOnly(value);
  }, []);

  const retry = useCallback(() => {
    setIsLoading(true);
    setReloadKey((key) => key + 1);
  }, []);

  return {
    items,
    unreadCount,
    isUnreadOnly,
    isLoading,
    isLoadingMore,
    hasMore,
    error,
    setUnreadOnly,
    loadMore,
    markRead,
    retry,
  };
}

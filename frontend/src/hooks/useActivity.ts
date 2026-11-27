"use client";

import { useCallback, useEffect, useState } from "react";
import useToast from "@/hooks/useToast";
import { apiClient } from "@/lib/apiClient";
import { getErrorMessage } from "@/lib/errorHandler";
import type { ActivityPage } from "@/types/api";

interface UseActivityResult {
  activity: ActivityPage | null;
  page: number;
  isLoading: boolean;
  error: string | null;
  hasPreviousPage: boolean;
  hasNextPage: boolean;
  reload: () => void;
  goToPreviousPage: () => void;
  goToNextPage: () => void;
}

export default function useActivity(boardId: string): UseActivityResult {
  const { showError } = useToast();
  const [page, setPage] = useState<number>(0);
  const [activity, setActivity] = useState<ActivityPage | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState<number>(0);

  useEffect(() => {
    let isActive = true;
    apiClient
      .listActivity(boardId, page)
      .then((loaded) => {
        if (!isActive) return;
        setActivity(loaded);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!isActive) return;
        setError(getErrorMessage(err, "Could not load the activity log."));
        showError(err, "Could not load the activity log.");
      })
      .finally(() => {
        if (isActive) setIsLoading(false);
      });
    return () => {
      isActive = false;
    };
  }, [boardId, page, reloadKey, showError]);

  const reload = useCallback(() => {
    setIsLoading(true);
    setReloadKey((key) => key + 1);
  }, []);

  const goToPreviousPage = useCallback(() => {
    setIsLoading(true);
    setPage((current) => Math.max(0, current - 1));
  }, []);

  const goToNextPage = useCallback(() => {
    setIsLoading(true);
    setPage((current) => current + 1);
  }, []);

  const hasNextPage =
    activity !== null && activity.items.length >= activity.pageSize;

  return {
    activity,
    page,
    isLoading,
    error,
    hasPreviousPage: page > 0,
    hasNextPage,
    reload,
    goToPreviousPage,
    goToNextPage,
  };
}

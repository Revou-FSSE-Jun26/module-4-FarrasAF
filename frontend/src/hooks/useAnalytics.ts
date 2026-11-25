"use client";

import { useCallback, useEffect, useState } from "react";
import useToast from "@/hooks/useToast";
import { apiClient } from "@/lib/apiClient";
import { getErrorMessage } from "@/lib/errorHandler";
import type { Analytics } from "@/types/api";

interface UseAnalyticsResult {
  analytics: Analytics | null;
  columnNames: Record<string, string>;
  isLoading: boolean;
  error: string | null;
  reload: () => void;
}

export default function useAnalytics(boardId: string): UseAnalyticsResult {
  const { showError } = useToast();
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [columnNames, setColumnNames] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState<number>(0);

  useEffect(() => {
    let isActive = true;
    Promise.all([apiClient.getAnalytics(boardId), apiClient.getBoard(boardId)])
      .then(([loaded, board]) => {
        if (!isActive) return;
        const names: Record<string, string> = {};
        for (const column of board.columns) names[column.id] = column.name;
        setAnalytics(loaded);
        setColumnNames(names);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!isActive) return;
        setError(getErrorMessage(err, "Could not load analytics."));
        showError(err, "Could not load analytics.");
      })
      .finally(() => {
        if (isActive) setIsLoading(false);
      });
    return () => {
      isActive = false;
    };
  }, [boardId, reloadKey, showError]);

  const reload = useCallback(() => {
    setIsLoading(true);
    setReloadKey((key) => key + 1);
  }, []);

  return { analytics, columnNames, isLoading, error, reload };
}

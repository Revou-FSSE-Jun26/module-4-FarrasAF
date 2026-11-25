"use client";

import { useCallback, useEffect, useState } from "react";
import useToast from "@/hooks/useToast";
import { apiClient } from "@/lib/apiClient";
import { getErrorMessage } from "@/lib/errorHandler";
import type { BoardDetail } from "@/types/api";

interface UseBoardResult {
  board: BoardDetail | null;
  isLoading: boolean;
  error: string | null;
  reload: () => void;
  refreshBoard: () => Promise<void>;
  setBoard: (board: BoardDetail) => void;
  addColumn: (name: string) => Promise<boolean>;
  renameColumn: (columnId: string, name: string) => Promise<boolean>;
  moveColumn: (columnId: string, targetIndex: number) => Promise<boolean>;
  deleteColumn: (columnId: string) => Promise<boolean>;
  addCard: (columnId: string, title: string) => Promise<boolean>;
}

export default function useBoard(boardId: string): UseBoardResult {
  const { showError } = useToast();
  const [board, setBoard] = useState<BoardDetail | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState<number>(0);

  useEffect(() => {
    let isActive = true;
    apiClient
      .getBoard(boardId)
      .then((loaded) => {
        if (!isActive) return;
        setBoard(loaded);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!isActive) return;
        setError(getErrorMessage(err, "Could not load this Board."));
        showError(err, "Could not load this Board.");
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

  const refreshBoard = useCallback(async () => {
    setBoard(await apiClient.getBoard(boardId));
  }, [boardId]);

  // Runs a mutation, then refetches so the server stays authoritative.
  const run = useCallback(
    async (action: () => Promise<unknown>, fallback: string) => {
      try {
        await action();
        setBoard(await apiClient.getBoard(boardId));
        return true;
      } catch (err: unknown) {
        showError(err, fallback);
        return false;
      }
    },
    [boardId, showError],
  );

  const addColumn = useCallback(
    (name: string) =>
      run(
        () => apiClient.createColumn(boardId, { name }),
        "Could not add the Column.",
      ),
    [boardId, run],
  );

  const renameColumn = useCallback(
    (columnId: string, name: string) =>
      run(
        () => apiClient.renameColumn(columnId, { name }),
        "Could not rename the Column.",
      ),
    [run],
  );

  const moveColumn = useCallback(
    (columnId: string, targetIndex: number) =>
      run(
        () => apiClient.reorderColumn(columnId, { targetIndex }),
        "Could not move the Column.",
      ),
    [run],
  );

  const deleteColumn = useCallback(
    (columnId: string) =>
      run(
        () => apiClient.deleteColumn(columnId),
        "Could not delete the Column. Only empty Columns can be deleted.",
      ),
    [run],
  );

  const addCard = useCallback(
    (columnId: string, title: string) =>
      run(
        () => apiClient.createCard(columnId, { title }),
        "Could not add the Card.",
      ),
    [run],
  );

  return {
    board,
    isLoading,
    error,
    reload,
    refreshBoard,
    setBoard,
    addColumn,
    renameColumn,
    moveColumn,
    deleteColumn,
    addCard,
  };
}

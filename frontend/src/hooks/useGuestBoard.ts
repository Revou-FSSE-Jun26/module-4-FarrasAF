"use client";

import { useCallback, useEffect, useState } from "react";
import useToast from "@/hooks/useToast";
import { apiClient, ApiError } from "@/lib/apiClient";
import type { GuestBoard, GuestComment } from "@/types/api";

export type GuestStatus = "loading" | "ready" | "unavailable" | "error";

interface UseGuestBoardResult {
  status: GuestStatus;
  board: GuestBoard | null;
  comments: GuestComment[];
  isCommentsLoading: boolean;
  hasCommentsError: boolean;
  selectedCardId: string | null;
  selectCardEvent: (cardId: string | null) => void;
  reload: () => void;
}

interface LoadedComments {
  cardId: string;
  items: GuestComment[];
  hasError: boolean;
}

export function useGuestBoard(token: string): UseGuestBoardResult {
  const { showError } = useToast();
  const [status, setStatus] = useState<GuestStatus>("loading");
  const [board, setBoard] = useState<GuestBoard | null>(null);
  const [loaded, setLoaded] = useState<LoadedComments | null>(null);
  const [selectedCardId, setSelectedCardId] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState<number>(0);

  useEffect(() => {
    let isCancelled = false;
    apiClient
      .getGuestBoard(token)
      .then((data) => {
        if (isCancelled) return;
        setBoard(data);
        setStatus("ready");
      })
      .catch((err: unknown) => {
        if (isCancelled) return;
        if (err instanceof ApiError && err.status === 403) {
          // One plain "link not available" message; no toast (frontend rule 24).
          setStatus("unavailable");
          return;
        }
        setStatus("error");
        showError(err, "Could not load this Board.");
      });
    return () => {
      isCancelled = true;
    };
  }, [token, reloadKey, showError]);

  useEffect(() => {
    if (selectedCardId === null) return;
    let isCancelled = false;
    apiClient
      .listGuestComments(token, selectedCardId)
      .then((data) => {
        if (!isCancelled) {
          setLoaded({
            cardId: selectedCardId,
            items: data.items,
            hasError: false,
          });
        }
      })
      .catch((err: unknown) => {
        if (isCancelled) return;
        if (err instanceof ApiError && err.status === 403) {
          setStatus("unavailable");
        } else {
          setLoaded({ cardId: selectedCardId, items: [], hasError: true });
          showError(err, "Could not load comments.");
        }
      });
    return () => {
      isCancelled = true;
    };
  }, [token, selectedCardId, showError]);

  const selectCardEvent = useCallback((cardId: string | null) => {
    setSelectedCardId(cardId);
  }, []);
  const reload = useCallback(() => {
    setStatus("loading");
    setReloadKey((k) => k + 1);
  }, []);
  const isCurrent = loaded !== null && loaded.cardId === selectedCardId;

  return {
    status,
    board,
    comments: isCurrent ? loaded.items : [],
    isCommentsLoading: selectedCardId !== null && !isCurrent,
    hasCommentsError: isCurrent && loaded.hasError,
    selectedCardId,
    selectCardEvent,
    reload,
  };
}

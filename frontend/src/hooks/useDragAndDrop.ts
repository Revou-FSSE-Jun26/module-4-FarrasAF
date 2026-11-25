"use client";

import { useCallback, useState } from "react";
import type { DragEndEvent, DragStartEvent } from "@dnd-kit/core";
import useToast from "@/hooks/useToast";
import { apiClient } from "@/lib/apiClient";
import { applyMove, canDragCards, computeDropTarget } from "@/lib/dragAndDrop";
import type { BoardDetail } from "@/types/api";

interface UseDragAndDropParams {
  board: BoardDetail | null;
  onBoardChange: (board: BoardDetail) => void;
}

interface UseDragAndDropResult {
  isDragEnabled: boolean;
  activeCardId: string | null;
  handleDragStart: (event: DragStartEvent) => void;
  handleDragEnd: (event: DragEndEvent) => void;
  handleDragCancel: () => void;
}

export default function useDragAndDrop({
  board,
  onBoardChange,
}: UseDragAndDropParams): UseDragAndDropResult {
  const { showError } = useToast();
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const isDragEnabled =
    board !== null &&
    board.status === "active" &&
    canDragCards(board.currentUserRole);

  const handleDragStart = useCallback(
    (event: DragStartEvent) => {
      if (isDragEnabled) setActiveCardId(String(event.active.id));
    },
    [isDragEnabled],
  );

  const handleDragCancel = useCallback(() => setActiveCardId(null), []);

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      setActiveCardId(null);
      if (!board || !isDragEnabled) return;

      const target = computeDropTarget(
        board.columns,
        String(event.active.id),
        event.over ? String(event.over.id) : null,
      );
      if (!target) return;

      const previous = board;
      // Optimistic update.
      onBoardChange({
        ...board,
        columns: applyMove(board.columns, target),
      });

      apiClient
        .moveCard(target.cardId, {
          targetColumnId: target.targetColumnId,
          targetIndex: target.targetIndex,
        })
        .then(
          () =>
            // The server state is authoritative; if this refetch fails the
            // optimistic state (already accepted by the server) stays.
            apiClient
              .getBoard(board.id)
              .then((fresh) => onBoardChange(fresh))
              .catch(() => undefined),
          (err: unknown) => {
            onBoardChange(previous);
            showError(err, "Could not move the Card. Your change was undone.");
          },
        );
    },
    [board, isDragEnabled, onBoardChange, showError],
  );

  return {
    isDragEnabled,
    activeCardId,
    handleDragStart,
    handleDragEnd,
    handleDragCancel,
  };
}

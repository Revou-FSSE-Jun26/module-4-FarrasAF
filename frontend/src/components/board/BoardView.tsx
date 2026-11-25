"use client";

import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  closestCorners,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import Link from "next/link";
import { useState } from "react";
import type { FormEvent } from "react";
import BoardColumnView from "@/components/board/BoardColumnView";
import CardDetailModal from "@/components/card/CardDetailModal";
import BaseButton from "@/components/shared/BaseButton";
import BaseEmptyState from "@/components/shared/BaseEmptyState";
import BaseErrorState from "@/components/shared/BaseErrorState";
import BaseInput from "@/components/shared/BaseInput";
import BaseLoadingState from "@/components/shared/BaseLoadingState";
import useBoard from "@/hooks/useBoard";
import useDragAndDrop from "@/hooks/useDragAndDrop";

interface BoardViewProps {
  boardId: string;
}

interface AddColumnFormProps {
  onColumnAdd: (name: string) => Promise<boolean>;
}

function AddColumnForm({ onColumnAdd }: AddColumnFormProps) {
  const [name, setName] = useState<string>("");
  const [error, setError] = useState<string | undefined>();
  const [isSaving, setIsSaving] = useState<boolean>(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = name.trim();
    if (trimmed.length < 1 || trimmed.length > 100) {
      setError("Column name must be 1 to 100 characters.");
      return;
    }
    setError(undefined);
    setIsSaving(true);
    try {
      if (await onColumnAdd(trimmed)) setName("");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      className="flex flex-col gap-2 rounded-lg border border-dashed border-gray-300 p-3"
    >
      <BaseInput
        label="Column name"
        value={name}
        error={error}
        maxLength={100}
        onChange={(e) => setName(e.target.value)}
      />
      <BaseButton type="submit" isLoading={isSaving}>
        Add column
      </BaseButton>
    </form>
  );
}

export default function BoardView({ boardId }: BoardViewProps) {
  const {
    board,
    isLoading,
    error,
    reload,
    refreshBoard,
    addColumn,
    renameColumn,
    moveColumn,
    deleteColumn,
    addCard,
    setBoard,
  } = useBoard(boardId);
  const { isDragEnabled, handleDragStart, handleDragEnd, handleDragCancel } =
    useDragAndDrop({ board, onBoardChange: setBoard });
  const [openCardId, setOpenCardId] = useState<string | null>(null);
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor),
  );

  if (isLoading) return <BaseLoadingState />;
  if (error || !board) {
    return (
      <BaseErrorState
        message={error ?? "Could not load this Board."}
        onRetry={reload}
      />
    );
  }

  const isAdmin = board.currentUserRole === "admin";
  const openCard =
    board.columns.flatMap((c) => c.cards).find((c) => c.id === openCardId) ??
    null;
  const columns = [...board.columns].sort(
    (a, b) => a.orderIndex - b.orderIndex,
  );

  return (
    <main className="flex flex-col gap-4 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-col gap-1">
          <Link
            href="/boards"
            className="text-sm text-blue-600 hover:underline"
          >
            Back to Boards
          </Link>
          <h1 className="text-xl font-semibold break-words text-gray-900">
            {board.name}
            {board.status === "archived" ? " (archived)" : ""}
          </h1>
        </div>
        <nav aria-label="Board" className="flex items-center gap-4">
          <Link
            href={`/boards/${board.id}/activity`}
            className="text-sm text-blue-600 hover:underline"
          >
            Activity
          </Link>
          <Link
            href={`/boards/${board.id}/analytics`}
            className="text-sm text-blue-600 hover:underline"
          >
            Analytics
          </Link>
          <Link
            href={`/boards/${board.id}/settings`}
            className="text-sm text-blue-600 hover:underline"
          >
            Board settings
          </Link>
        </nav>
      </div>

      {columns.length === 0 ? (
        <BaseEmptyState
          message={
            isAdmin
              ? "This Board has no Columns yet. Add one to get started."
              : "This Board has no Columns yet."
          }
        />
      ) : null}

      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        onDragCancel={handleDragCancel}
      >
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start">
          {columns.map((column, index) => (
            <BoardColumnView
              key={column.id}
              column={column}
              isAdmin={isAdmin}
              isDragEnabled={isDragEnabled}
              isFirst={index === 0}
              isLast={index === columns.length - 1}
              onColumnRename={(name) => renameColumn(column.id, name)}
              onColumnMove={(offset) => moveColumn(column.id, index + offset)}
              onColumnDelete={() => deleteColumn(column.id)}
              onCardAdd={(title) => addCard(column.id, title)}
              onCardOpen={setOpenCardId}
            />
          ))}
          {isAdmin ? (
            <div className="w-full lg:min-w-0 lg:flex-1">
              <AddColumnForm onColumnAdd={addColumn} />
            </div>
          ) : null}
        </div>
      </DndContext>

      {openCard ? (
        <CardDetailModal
          key={openCard.id}
          boardId={board.id}
          card={openCard}
          onCardChange={refreshBoard}
          onClose={() => setOpenCardId(null)}
        />
      ) : null}
    </main>
  );
}

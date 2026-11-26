"use client";

import {
  DndContext,
  DragOverlay,
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
import CardItem from "@/components/card/CardItem";
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
      className="flex flex-col gap-2.5 rounded-xl border border-dashed border-slate-300/90 bg-slate-100/50 p-3.5 transition-colors hover:border-slate-300 hover:bg-slate-100/80"
    >
      <BaseInput
        label="Column name"
        placeholder="e.g. In Review"
        value={name}
        error={error}
        maxLength={100}
        onChange={(e) => setName(e.target.value)}
      />
      <BaseButton type="submit" variant="secondary" isLoading={isSaving}>
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
  const {
    isDragEnabled,
    activeCardId,
    handleDragStart,
    handleDragEnd,
    handleDragCancel,
  } = useDragAndDrop({ board, onBoardChange: setBoard });
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
  const allCards = board.columns.flatMap((c) => c.cards);
  const openCard = allCards.find((c) => c.id === openCardId) ?? null;
  const activeCard = allCards.find((c) => c.id === activeCardId) ?? null;
  const columns = [...board.columns].sort(
    (a, b) => a.orderIndex - b.orderIndex,
  );

  return (
    <main className="flex flex-1 flex-col gap-5 p-4 lg:p-6">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200/80 pb-4">
        <div className="flex flex-col gap-1">
          <Link
            href="/boards"
            className="inline-flex w-fit items-center gap-1 text-xs font-medium text-slate-500 transition-colors hover:text-indigo-600"
          >
            <svg
              aria-hidden="true"
              viewBox="0 0 20 20"
              fill="currentColor"
              className="size-3.5"
            >
              <path
                fillRule="evenodd"
                d="M11.78 5.22a.75.75 0 0 1 0 1.06L8.06 10l3.72 3.72a.75.75 0 1 1-1.06 1.06l-4.25-4.25a.75.75 0 0 1 0-1.06l4.25-4.25a.75.75 0 0 1 1.06 0Z"
                clipRule="evenodd"
              />
            </svg>
            Back to Boards
          </Link>
          <div className="flex flex-wrap items-center gap-2.5">
            <h1 className="text-xl font-semibold tracking-tight break-words text-slate-900">
              {board.name}
              {board.status === "archived" ? " (archived)" : ""}
            </h1>
            {board.status === "archived" ? (
              <span className="rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-800 ring-1 ring-amber-200">
                Archived
              </span>
            ) : null}
          </div>
        </div>
        <nav
          aria-label="Board"
          className="inline-flex flex-wrap items-center gap-1 rounded-lg border border-slate-200/80 bg-white p-1 shadow-2xs"
        >
          <Link
            href={`/boards/${board.id}/activity`}
            className="rounded-md px-3 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900"
          >
            Activity
          </Link>
          <Link
            href={`/boards/${board.id}/analytics`}
            className="rounded-md px-3 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900"
          >
            Analytics
          </Link>
          <Link
            href={`/boards/${board.id}/settings`}
            className="rounded-md px-3 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900"
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
        <DragOverlay>
          {activeCard ? <CardItem card={activeCard} isOverlay /> : null}
        </DragOverlay>
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

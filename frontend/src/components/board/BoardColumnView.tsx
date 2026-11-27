"use client";

import { useDroppable } from "@dnd-kit/core";
import {
  SortableContext,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { useState } from "react";
import type { FormEvent } from "react";
import AddCardForm from "@/components/card/AddCardForm";
import CardItem from "@/components/card/CardItem";
import SortableCardItem from "@/components/card/SortableCardItem";
import BaseButton from "@/components/shared/BaseButton";
import BaseInput from "@/components/shared/BaseInput";
import BaseModal from "@/components/shared/BaseModal";
import type { BoardColumn } from "@/types/api";

interface BoardColumnViewProps {
  column: BoardColumn;
  isAdmin: boolean;
  isDragEnabled: boolean;
  isFirst: boolean;
  isLast: boolean;
  onColumnRename: (name: string) => Promise<boolean>;
  onColumnMove: (offset: -1 | 1) => Promise<boolean>;
  onColumnDelete: () => Promise<boolean>;
  onCardAdd: (title: string) => Promise<boolean>;
  onCardOpen: (cardId: string) => void;
}

export default function BoardColumnView({
  column,
  isAdmin,
  isDragEnabled,
  isFirst,
  isLast,
  onColumnRename,
  onColumnMove,
  onColumnDelete,
  onCardAdd,
  onCardOpen,
}: BoardColumnViewProps) {
  const { setNodeRef: setDropRef, isOver } = useDroppable({
    id: column.id,
    disabled: !isDragEnabled,
  });
  const [isRenaming, setIsRenaming] = useState<boolean>(false);
  const [name, setName] = useState<string>(column.name);
  const [renameError, setRenameError] = useState<string | undefined>();
  const [isConfirmingDelete, setIsConfirmingDelete] = useState<boolean>(false);
  const [isBusy, setIsBusy] = useState<boolean>(false);

  const cards = [...column.cards].sort((a, b) => a.orderIndex - b.orderIndex);

  async function handleRename(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = name.trim();
    if (trimmed.length < 1 || trimmed.length > 100) {
      setRenameError("Column name must be 1 to 100 characters.");
      return;
    }
    setRenameError(undefined);
    setIsBusy(true);
    try {
      if (await onColumnRename(trimmed)) setIsRenaming(false);
    } finally {
      setIsBusy(false);
    }
  }

  async function handleDelete() {
    setIsBusy(true);
    try {
      await onColumnDelete();
      setIsConfirmingDelete(false);
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <section
      aria-label={column.name}
      className={`group/col flex w-full flex-col gap-3 rounded-2xl border-[1.5px] p-3.5 shadow-[3px_3px_0_#211621] transition-colors lg:min-w-0 lg:flex-1 ${
        isOver
          ? "border-[#211621] bg-[#d9ff43]/40 ring-2 ring-[#ff7965]"
          : "border-[#211621] bg-[#e8dfca]"
      }`}
    >
      {isRenaming ? (
        <form
          onSubmit={handleRename}
          noValidate
          className="flex flex-col gap-2 rounded-lg border border-slate-200 bg-white p-2.5 shadow-2xs"
        >
          <BaseInput
            label="Column name"
            value={name}
            error={renameError}
            maxLength={100}
            onChange={(e) => setName(e.target.value)}
          />
          <div className="flex gap-2">
            <BaseButton type="submit" size="sm" isLoading={isBusy}>
              Save
            </BaseButton>
            <BaseButton
              variant="secondary"
              size="sm"
              onClick={() => {
                setName(column.name);
                setRenameError(undefined);
                setIsRenaming(false);
              }}
            >
              Cancel
            </BaseButton>
          </div>
        </form>
      ) : (
        <div className="flex items-start justify-between gap-2 px-1">
          <div className="flex min-w-0 items-center gap-2 pt-0.5">
            <h2 className="font-mono text-[12px] font-semibold uppercase tracking-[0.06em] break-words text-slate-800">
              {column.name}
            </h2>
            <span className="shrink-0 rounded-full border border-[#211621] bg-[#c9b7ef] px-2 py-0.5 text-[11px] font-bold text-[#211621] tabular-nums">
              {cards.length}
            </span>
          </div>
          {isAdmin ? (
            <div className="flex shrink-0 items-center gap-0.5 transition-opacity lg:opacity-65 lg:group-hover/col:opacity-100 lg:focus-within:opacity-100">
              <button
                type="button"
                aria-label={`Rename ${column.name}`}
                title="Rename column"
                onClick={() => setIsRenaming(true)}
                className="inline-flex size-7 items-center justify-center rounded-md text-slate-500 transition-colors hover:bg-slate-200/80 hover:text-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
              >
                <svg
                  aria-hidden="true"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  className="size-3.5"
                >
                  <path d="m5.433 13.917 1.262-3.155A4 4 0 0 1 7.58 9.42l6.92-6.918a2.121 2.121 0 0 1 3 3l-6.92 6.918c-.383.383-.84.685-1.343.886l-3.154 1.262a.5.5 0 0 1-.65-.65Z" />
                  <path d="M3.5 5.75c0-.69.56-1.25 1.25-1.25H10A.75.75 0 0 0 10 3H4.75A2.75 2.75 0 0 0 2 5.75v9.5A2.75 2.75 0 0 0 4.75 18h9.5A2.75 2.75 0 0 0 17 15.25V10a.75.75 0 0 0-1.5 0v5.25c0 .69-.56 1.25-1.25 1.25h-9.5c-.69 0-1.25-.56-1.25-1.25v-9.5Z" />
                </svg>
              </button>
              <button
                type="button"
                aria-label={`Move ${column.name} earlier`}
                title="Move column earlier"
                disabled={isFirst}
                onClick={() => void onColumnMove(-1)}
                className="inline-flex size-7 items-center justify-center rounded-md text-slate-500 transition-colors hover:bg-slate-200/80 hover:text-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 disabled:cursor-not-allowed disabled:opacity-30"
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
              </button>
              <button
                type="button"
                aria-label={`Move ${column.name} later`}
                title="Move column later"
                disabled={isLast}
                onClick={() => void onColumnMove(1)}
                className="inline-flex size-7 items-center justify-center rounded-md text-slate-500 transition-colors hover:bg-slate-200/80 hover:text-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 disabled:cursor-not-allowed disabled:opacity-30"
              >
                <svg
                  aria-hidden="true"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  className="size-3.5"
                >
                  <path
                    fillRule="evenodd"
                    d="M8.22 5.22a.75.75 0 0 1 1.06 0l4.25 4.25a.75.75 0 0 1 0 1.06l-4.25 4.25a.75.75 0 0 1-1.06-1.06L11.94 10 8.22 6.28a.75.75 0 0 1 0-1.06Z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
              <button
                type="button"
                aria-label={`Delete ${column.name}`}
                title="Delete column"
                onClick={() => setIsConfirmingDelete(true)}
                className="inline-flex size-7 items-center justify-center rounded-md text-slate-400 transition-colors hover:bg-rose-50 hover:text-rose-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-rose-500"
              >
                <svg
                  aria-hidden="true"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  className="size-3.5"
                >
                  <path
                    fillRule="evenodd"
                    d="M8.75 1A2.75 2.75 0 0 0 6 3.75v.443c-.795.077-1.584.176-2.365.298a.75.75 0 1 0 .23 1.482l.149-.022.841 10.518A2.75 2.75 0 0 0 7.596 19h4.807a2.75 2.75 0 0 0 2.742-2.53l.841-10.52.149.023a.75.75 0 0 0 .23-1.482A41.03 41.03 0 0 0 14 4.193V3.75A2.75 2.75 0 0 0 11.25 1h-2.5ZM10 4c.84 0 1.673.025 2.5.075V3.75c0-.69-.56-1.25-1.25-1.25h-2.5c-.69 0-1.25.56-1.25 1.25v.325C8.327 4.025 9.16 4 10 4ZM8.58 7.72a.75.75 0 0 0-1.5.06l.3 7.5a.75.75 0 1 0 1.5-.06l-.3-7.5Zm4.34.06a.75.75 0 1 0-1.5-.06l-.3 7.5a.75.75 0 1 0 1.5.06l.3-7.5Z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </div>
          ) : null}
        </div>
      )}

      <div
        ref={setDropRef}
        className="kanban-scroll flex min-h-12 flex-col gap-2 lg:max-h-[calc(100vh-16rem)] lg:overflow-y-auto lg:pr-0.5"
      >
        {cards.length === 0 ? (
          <p
            className={`rounded-lg border border-dashed px-3 py-5 text-center text-xs transition-colors ${
              isOver
                ? "border-indigo-300 bg-indigo-50/70 text-indigo-600"
                : "border-slate-200/90 text-slate-400"
            }`}
          >
            No cards yet
          </p>
        ) : isDragEnabled ? (
          <SortableContext
            items={cards.map((card) => card.id)}
            strategy={verticalListSortingStrategy}
          >
            <ul className="flex flex-col gap-2">
              {cards.map((card) => (
                <SortableCardItem
                  key={card.id}
                  card={card}
                  onCardOpen={onCardOpen}
                />
              ))}
            </ul>
          </SortableContext>
        ) : (
          <ul className="flex flex-col gap-2">
            {cards.map((card) => (
              <CardItem key={card.id} card={card} onCardOpen={onCardOpen} />
            ))}
          </ul>
        )}
      </div>

      <AddCardForm columnName={column.name} onCardAdd={onCardAdd} />

      <BaseModal
        isOpen={isConfirmingDelete}
        title="Delete Column"
        onClose={() => setIsConfirmingDelete(false)}
      >
        <p className="mb-4 text-sm text-slate-600">
          Delete the Column &quot;{column.name}&quot;? Only empty Columns can be
          deleted.
        </p>
        <div className="flex justify-end gap-2">
          <BaseButton
            variant="secondary"
            onClick={() => setIsConfirmingDelete(false)}
          >
            Cancel
          </BaseButton>
          <BaseButton
            variant="danger"
            isLoading={isBusy}
            onClick={() => void handleDelete()}
          >
            Delete
          </BaseButton>
        </div>
      </BaseModal>
    </section>
  );
}

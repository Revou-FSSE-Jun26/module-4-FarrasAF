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
  const { setNodeRef: setDropRef } = useDroppable({
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
      className="flex w-full flex-col gap-3 rounded-lg bg-gray-100 p-3 lg:min-w-0 lg:flex-1"
    >
      {isRenaming ? (
        <form
          onSubmit={handleRename}
          noValidate
          className="flex flex-col gap-2"
        >
          <BaseInput
            label="Column name"
            value={name}
            error={renameError}
            maxLength={100}
            onChange={(e) => setName(e.target.value)}
          />
          <div className="flex gap-2">
            <BaseButton type="submit" isLoading={isBusy}>
              Save
            </BaseButton>
            <BaseButton
              variant="secondary"
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
        <div className="flex flex-col gap-2">
          <h2 className="text-sm font-semibold break-words text-gray-900">
            {column.name}{" "}
            <span className="font-normal text-gray-600">({cards.length})</span>
          </h2>
          {isAdmin ? (
            <div className="flex flex-wrap gap-1">
              <BaseButton
                variant="secondary"
                aria-label={`Rename ${column.name}`}
                onClick={() => setIsRenaming(true)}
              >
                Rename
              </BaseButton>
              <BaseButton
                variant="secondary"
                aria-label={`Move ${column.name} earlier`}
                disabled={isFirst}
                onClick={() => void onColumnMove(-1)}
              >
                Move up
              </BaseButton>
              <BaseButton
                variant="secondary"
                aria-label={`Move ${column.name} later`}
                disabled={isLast}
                onClick={() => void onColumnMove(1)}
              >
                Move down
              </BaseButton>
              <BaseButton
                variant="danger"
                aria-label={`Delete ${column.name}`}
                onClick={() => setIsConfirmingDelete(true)}
              >
                Delete
              </BaseButton>
            </div>
          ) : null}
        </div>
      )}

      <div ref={setDropRef} className="flex min-h-12 flex-col gap-2">
        {cards.length === 0 ? (
          <p className="text-sm text-gray-600">No cards yet</p>
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
        <p className="mb-4 text-sm text-gray-700">
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

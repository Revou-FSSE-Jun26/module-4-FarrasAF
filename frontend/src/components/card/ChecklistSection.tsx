"use client";

import { useState } from "react";
import type { KeyboardEvent } from "react";
import ChecklistItemRow from "@/components/card/ChecklistItemRow";
import BaseButton from "@/components/shared/BaseButton";
import useChecklist from "@/hooks/useChecklist";
import { CHECKLIST_MAX_ITEMS, CHECKLIST_TEXT_MAX } from "@/lib/checklist";
import type { ChecklistItem } from "@/types/api";

interface ChecklistSectionProps {
  cardId: string;
  items: ChecklistItem[];
  onChecklistChange: () => Promise<void>;
}

export default function ChecklistSection({
  cardId,
  items,
  onChecklistChange,
}: ChecklistSectionProps) {
  const { isBusy, addItem, setItemDone, renameItem, removeItem } = useChecklist(
    { cardId, onChecklistChange },
  );
  const [text, setText] = useState<string>("");
  const [error, setError] = useState<string | undefined>();

  const doneCount = items.filter((item) => item.isDone).length;
  const isFull = items.length >= CHECKLIST_MAX_ITEMS;

  async function handleAdd() {
    const trimmed = text.trim();
    if (trimmed.length < 1 || trimmed.length > CHECKLIST_TEXT_MAX) {
      setError(`To-do text must be 1 to ${CHECKLIST_TEXT_MAX} characters.`);
      return;
    }
    setError(undefined);
    if (await addItem(trimmed)) setText("");
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    // The section sits inside the Card form: Enter adds the item, not the Card save.
    if (event.key === "Enter") {
      event.preventDefault();
      void handleAdd();
    }
  }

  return (
    <section aria-label="To-do list" className="flex flex-col gap-2.5">
      <div className="flex items-baseline justify-between gap-2">
        <h3 className="text-sm font-medium text-slate-700">To-do list</h3>
        {items.length > 0 ? (
          <span className="text-xs text-slate-500 tabular-nums">
            {doneCount}/{items.length} done
          </span>
        ) : null}
      </div>
      {items.length > 0 ? (
        <ul className="flex flex-col gap-1.5">
          {items.map((item) => (
            <ChecklistItemRow
              key={item.id}
              item={item}
              isDisabled={isBusy}
              onItemToggle={(isDone) => setItemDone(item.id, isDone)}
              onItemRename={(value) => renameItem(item.id, value)}
              onItemRemove={() => removeItem(item.id)}
            />
          ))}
        </ul>
      ) : (
        <p className="text-xs text-slate-400">No to-do items yet.</p>
      )}
      {isFull ? (
        <p className="text-xs text-slate-500">
          A Card can have at most {CHECKLIST_MAX_ITEMS} to-do items.
        </p>
      ) : (
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-2">
            <input
              type="text"
              aria-label="New to-do item"
              placeholder="Add a to-do item..."
              value={text}
              maxLength={CHECKLIST_TEXT_MAX}
              aria-invalid={error ? true : undefined}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={handleKeyDown}
              className="min-h-10 min-w-0 flex-1 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-2xs focus:outline-none focus-visible:border-indigo-500 focus-visible:ring-2 focus-visible:ring-indigo-500/25"
            />
            <BaseButton
              variant="secondary"
              isLoading={isBusy}
              onClick={() => void handleAdd()}
            >
              Add
            </BaseButton>
          </div>
          {error ? (
            <p role="alert" className="text-xs font-medium text-rose-600">
              {error}
            </p>
          ) : null}
        </div>
      )}
    </section>
  );
}

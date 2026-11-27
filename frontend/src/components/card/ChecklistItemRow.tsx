"use client";

import { useState } from "react";
import type { KeyboardEvent } from "react";
import BaseButton from "@/components/shared/BaseButton";
import { CHECKLIST_TEXT_MAX } from "@/lib/checklist";
import type { ChecklistItem } from "@/types/api";

interface ChecklistItemRowProps {
  item: ChecklistItem;
  isDisabled: boolean;
  onItemToggle: (isDone: boolean) => Promise<boolean>;
  onItemRename: (text: string) => Promise<boolean>;
  onItemRemove: () => Promise<boolean>;
}

export default function ChecklistItemRow({
  item,
  isDisabled,
  onItemToggle,
  onItemRename,
  onItemRemove,
}: ChecklistItemRowProps) {
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [draft, setDraft] = useState<string>(item.text);
  const [error, setError] = useState<string | undefined>();

  function startEditing() {
    setDraft(item.text);
    setError(undefined);
    setIsEditing(true);
  }

  async function saveEdit() {
    const trimmed = draft.trim();
    if (trimmed.length < 1 || trimmed.length > CHECKLIST_TEXT_MAX) {
      setError(`To-do text must be 1 to ${CHECKLIST_TEXT_MAX} characters.`);
      return;
    }
    if (trimmed === item.text) {
      setIsEditing(false);
      return;
    }
    if (await onItemRename(trimmed)) setIsEditing(false);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    // The row sits inside the Card form: Enter must not submit that form.
    if (event.key === "Enter") {
      event.preventDefault();
      void saveEdit();
    } else if (event.key === "Escape") {
      event.preventDefault();
      event.stopPropagation();
      setIsEditing(false);
    }
  }

  if (isEditing) {
    return (
      <li className="flex flex-col gap-1.5">
        <div className="flex items-center gap-2">
          <input
            type="text"
            aria-label="To-do text"
            value={draft}
            maxLength={CHECKLIST_TEXT_MAX}
            aria-invalid={error ? true : undefined}
            autoFocus
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={handleKeyDown}
            className="min-h-8 min-w-0 flex-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-sm text-slate-900 focus:outline-none focus-visible:border-indigo-500 focus-visible:ring-2 focus-visible:ring-indigo-500/25"
          />
          <BaseButton
            size="sm"
            disabled={isDisabled}
            onClick={() => void saveEdit()}
          >
            Save
          </BaseButton>
          <BaseButton
            size="sm"
            variant="secondary"
            onClick={() => setIsEditing(false)}
          >
            Cancel
          </BaseButton>
        </div>
        {error ? (
          <p role="alert" className="text-xs font-medium text-rose-600">
            {error}
          </p>
        ) : null}
      </li>
    );
  }

  return (
    <li className="flex items-center gap-2">
      <input
        type="checkbox"
        checked={item.isDone}
        disabled={isDisabled}
        aria-label={item.text}
        onChange={(e) => void onItemToggle(e.target.checked)}
        className="size-4 shrink-0 accent-indigo-600"
      />
      <span
        className={`min-w-0 flex-1 text-sm break-words ${
          item.isDone ? "text-slate-400 line-through" : "text-slate-900"
        }`}
      >
        {item.text}
      </span>
      <BaseButton
        size="sm"
        variant="ghost"
        disabled={isDisabled}
        aria-label={`Edit ${item.text}`}
        onClick={startEditing}
      >
        Edit
      </BaseButton>
      <BaseButton
        size="sm"
        variant="ghost"
        disabled={isDisabled}
        aria-label={`Delete ${item.text}`}
        onClick={() => void onItemRemove()}
      >
        Delete
      </BaseButton>
    </li>
  );
}

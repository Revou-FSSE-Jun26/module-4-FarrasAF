"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import BaseButton from "@/components/shared/BaseButton";
import BaseInput from "@/components/shared/BaseInput";

interface AddCardFormProps {
  columnName: string;
  onCardAdd: (title: string) => Promise<boolean>;
}

export default function AddCardForm({
  columnName,
  onCardAdd,
}: AddCardFormProps) {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [title, setTitle] = useState<string>("");
  const [error, setError] = useState<string | undefined>();
  const [isSaving, setIsSaving] = useState<boolean>(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = title.trim();
    if (trimmed.length < 1 || trimmed.length > 255) {
      setError("Card title must be 1 to 255 characters.");
      return;
    }
    setError(undefined);
    setIsSaving(true);
    try {
      if (await onCardAdd(trimmed)) {
        setTitle("");
        setIsOpen(false);
      }
    } finally {
      setIsSaving(false);
    }
  }

  if (!isOpen) {
    return (
      <BaseButton
        variant="ghost"
        size="sm"
        aria-label={`Add card to ${columnName}`}
        className="w-full justify-start text-slate-600 hover:bg-slate-200/70 hover:text-slate-900"
        onClick={() => setIsOpen(true)}
      >
        <svg
          aria-hidden="true"
          viewBox="0 0 20 20"
          fill="currentColor"
          className="size-4"
        >
          <path d="M10.75 4.75a.75.75 0 0 0-1.5 0v4.5h-4.5a.75.75 0 0 0 0 1.5h4.5v4.5a.75.75 0 0 0 1.5 0v-4.5h4.5a.75.75 0 0 0 0-1.5h-4.5v-4.5Z" />
        </svg>
        Add card
      </BaseButton>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      className="flex flex-col gap-2.5 rounded-lg border border-slate-200 bg-white p-2.5 shadow-2xs"
    >
      <BaseInput
        label="Card title"
        placeholder="Enter a title for this card..."
        value={title}
        error={error}
        maxLength={255}
        onChange={(e) => setTitle(e.target.value)}
      />
      <div className="flex gap-2">
        <BaseButton type="submit" size="sm" isLoading={isSaving}>
          Add
        </BaseButton>
        <BaseButton
          variant="secondary"
          size="sm"
          onClick={() => setIsOpen(false)}
        >
          Cancel
        </BaseButton>
      </div>
    </form>
  );
}

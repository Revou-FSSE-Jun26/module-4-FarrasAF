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
        variant="secondary"
        aria-label={`Add card to ${columnName}`}
        onClick={() => setIsOpen(true)}
      >
        Add card
      </BaseButton>
    );
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-2">
      <BaseInput
        label="Card title"
        value={title}
        error={error}
        maxLength={255}
        onChange={(e) => setTitle(e.target.value)}
      />
      <div className="flex gap-2">
        <BaseButton type="submit" isLoading={isSaving}>
          Add
        </BaseButton>
        <BaseButton variant="secondary" onClick={() => setIsOpen(false)}>
          Cancel
        </BaseButton>
      </div>
    </form>
  );
}

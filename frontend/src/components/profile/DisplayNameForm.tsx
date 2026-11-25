"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import BaseButton from "@/components/shared/BaseButton";
import BaseInput from "@/components/shared/BaseInput";

interface DisplayNameFormProps {
  initialDisplayName: string;
  error?: string;
  isSaving: boolean;
  onDisplayNameSave: (displayName: string) => Promise<boolean>;
}

export default function DisplayNameForm({
  initialDisplayName,
  error,
  isSaving,
  onDisplayNameSave,
}: DisplayNameFormProps) {
  const [displayName, setDisplayName] = useState<string>(initialDisplayName);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const isSaved = await onDisplayNameSave(displayName);
    if (isSaved) setDisplayName(displayName.trim());
  }

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      className="flex flex-col gap-4 rounded-lg border border-gray-200 bg-white p-6"
    >
      <h2 className="text-lg font-semibold text-gray-900">Display name</h2>
      <BaseInput
        label="Display name"
        autoComplete="nickname"
        value={displayName}
        error={error}
        onChange={(e) => setDisplayName(e.target.value)}
      />
      <BaseButton type="submit" isLoading={isSaving} className="self-start">
        Save display name
      </BaseButton>
    </form>
  );
}

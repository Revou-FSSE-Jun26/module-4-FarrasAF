"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import BaseButton from "@/components/shared/BaseButton";
import BaseInput from "@/components/shared/BaseInput";
import useToast from "@/hooks/useToast";

interface CreateTeamFormProps {
  onTeamCreate: (name: string) => Promise<unknown>;
}

export default function CreateTeamForm({ onTeamCreate }: CreateTeamFormProps) {
  const { showError } = useToast();
  const [name, setName] = useState<string>("");
  const [error, setError] = useState<string | undefined>();
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = name.trim();
    if (trimmed.length < 1 || trimmed.length > 100) {
      setError("Team name must be 1 to 100 characters.");
      return;
    }
    setError(undefined);
    setIsSubmitting(true);
    try {
      await onTeamCreate(trimmed);
      setName("");
    } catch (err: unknown) {
      showError(err, "Could not create Team.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      className="flex flex-col gap-2 lg:flex-row lg:items-center"
    >
      <BaseInput
        label="Team name"
        value={name}
        error={error}
        onChange={(e) => setName(e.target.value)}
      />
      <BaseButton
        type="submit"
        isLoading={isSubmitting}
        className="h-10 shrink-0 whitespace-nowrap"
      >
        Create Team
      </BaseButton>
    </form>
  );
}

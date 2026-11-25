"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import BaseButton from "@/components/shared/BaseButton";
import BaseInput from "@/components/shared/BaseInput";
import useToast from "@/hooks/useToast";
import type { Team } from "@/types/api";

interface CreateBoardFormProps {
  teams: Team[];
  onBoardCreate: (teamId: string, name: string) => Promise<unknown>;
}

export default function CreateBoardForm({
  teams,
  onBoardCreate,
}: CreateBoardFormProps) {
  const { showError } = useToast();
  const [name, setName] = useState<string>("");
  const [teamId, setTeamId] = useState<string>("");
  const [error, setError] = useState<string | undefined>();
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const selectedTeamId = teamId || teams[0]?.id || "";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = name.trim();
    if (!selectedTeamId) {
      setError("Join or create a Team first.");
      return;
    }
    if (trimmed.length < 1 || trimmed.length > 100) {
      setError("Board name must be 1 to 100 characters.");
      return;
    }
    setError(undefined);
    setIsSubmitting(true);
    try {
      await onBoardCreate(selectedTeamId, trimmed);
      setName("");
    } catch (err: unknown) {
      showError(err, "Could not create Board.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      className="flex flex-col gap-2 lg:flex-row lg:items-end"
    >
      <BaseInput
        label="Board name"
        value={name}
        error={error}
        onChange={(e) => setName(e.target.value)}
      />
      <div className="flex w-full flex-col gap-1">
        <label
          htmlFor="create-board-team"
          className="text-sm font-medium text-gray-900"
        >
          Team
        </label>
        <select
          id="create-board-team"
          value={selectedTeamId}
          onChange={(e) => setTeamId(e.target.value)}
          className="min-h-10 w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900"
        >
          {teams.map((team) => (
            <option key={team.id} value={team.id}>
              {team.name}
            </option>
          ))}
        </select>
      </div>
      <BaseButton type="submit" isLoading={isSubmitting}>
        Create Board
      </BaseButton>
    </form>
  );
}

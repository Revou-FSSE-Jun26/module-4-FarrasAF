"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import type { FormEvent } from "react";
import BoardMemberPanel from "@/components/board/BoardMemberPanel";
import InvitationLinkPanel from "@/components/board/InvitationLinkPanel";
import BaseButton from "@/components/shared/BaseButton";
import BaseErrorState from "@/components/shared/BaseErrorState";
import BaseInput from "@/components/shared/BaseInput";
import BaseLoadingState from "@/components/shared/BaseLoadingState";
import BaseModal from "@/components/shared/BaseModal";
import { useBoardSettings } from "@/hooks/useBoards";
import type { Board, BoardVisibility } from "@/types/api";

interface BoardSettingsViewProps {
  boardId: string;
}

interface BoardEditFormProps {
  board: Board;
  onBoardSave: (
    name: string,
    description: string,
    visibility: BoardVisibility,
  ) => Promise<boolean>;
}

function BoardEditForm({ board, onBoardSave }: BoardEditFormProps) {
  const [name, setName] = useState<string>(board.name);
  const [description, setDescription] = useState<string>(board.description);
  const [visibility, setVisibility] = useState<BoardVisibility>(
    board.visibility,
  );
  const [error, setError] = useState<string | undefined>();
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [isSaved, setIsSaved] = useState<boolean>(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = name.trim();
    if (trimmed.length < 1 || trimmed.length > 100) {
      setError("Board name must be 1 to 100 characters.");
      return;
    }
    setError(undefined);
    setIsSaved(false);
    setIsSaving(true);
    try {
      setIsSaved(await onBoardSave(trimmed, description, visibility));
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-3">
      <BaseInput
        label="Board name"
        value={name}
        error={error}
        onChange={(e) => setName(e.target.value)}
      />
      <div className="flex flex-col gap-1">
        <label
          htmlFor="board-description"
          className="text-sm font-medium text-gray-900"
        >
          Description
        </label>
        <textarea
          id="board-description"
          value={description}
          rows={3}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900"
        />
      </div>
      <div className="flex flex-col gap-1">
        <label
          htmlFor="board-visibility"
          className="text-sm font-medium text-gray-900"
        >
          Visibility
        </label>
        <select
          id="board-visibility"
          value={visibility}
          onChange={(e) =>
            setVisibility(e.target.value === "team" ? "team" : "private")
          }
          className="min-h-10 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="private">Private</option>
          <option value="team">Team</option>
        </select>
      </div>
      <div className="flex items-center gap-3">
        <BaseButton type="submit" isLoading={isSaving}>
          Save changes
        </BaseButton>
        {isSaved ? (
          <span role="status" className="text-sm text-green-700">
            Saved
          </span>
        ) : null}
      </div>
    </form>
  );
}

export default function BoardSettingsView({ boardId }: BoardSettingsViewProps) {
  const router = useRouter();
  const settings = useBoardSettings(boardId);
  const { board, isLoading, error, reload } = settings;
  const [isConfirmingDelete, setIsConfirmingDelete] = useState<boolean>(false);
  const [isBusy, setIsBusy] = useState<boolean>(false);

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
  const isArchived = board.status === "archived";

  async function handleSave(
    name: string,
    description: string,
    visibility: BoardVisibility,
  ): Promise<boolean> {
    return settings.updateBoard({ name, description, visibility });
  }

  async function handleDelete() {
    setIsBusy(true);
    const isDeleted = await settings.deleteBoard();
    setIsBusy(false);
    if (isDeleted) router.push("/boards");
    else setIsConfirmingDelete(false);
  }

  return (
    <main className="rt-page max-w-5xl">
      <div className="flex flex-col gap-1">
        <Link href="/boards" className="text-sm text-blue-600 hover:underline">
          Back to Boards
        </Link>
        <h1 className="text-xl font-semibold text-gray-900">
          {board.name} settings
          {isArchived ? " (archived)" : ""}
        </h1>
      </div>

      {isAdmin ? (
        <>
          <section
            aria-labelledby="details-heading"
            className="flex flex-col gap-3"
          >
            <h2 id="details-heading" className="text-lg font-semibold">
              Details
            </h2>
            <BoardEditForm
              key={board.id}
              board={board}
              onBoardSave={handleSave}
            />
          </section>

          <section
            aria-labelledby="lifecycle-heading"
            className="flex flex-col gap-3"
          >
            <h2 id="lifecycle-heading" className="text-lg font-semibold">
              Board lifecycle
            </h2>
            <div className="flex flex-wrap gap-2">
              {isArchived ? (
                <BaseButton
                  variant="secondary"
                  onClick={() => void settings.restoreBoard()}
                >
                  Restore Board
                </BaseButton>
              ) : (
                <BaseButton
                  variant="secondary"
                  onClick={() => void settings.archiveBoard()}
                >
                  Archive Board
                </BaseButton>
              )}
              <BaseButton
                variant="danger"
                onClick={() => setIsConfirmingDelete(true)}
              >
                Delete Board
              </BaseButton>
            </div>
          </section>
        </>
      ) : (
        <p className="text-sm text-gray-600">
          Only Board admins can change these settings.
        </p>
      )}

      <BoardMemberPanel
        members={settings.members}
        addableMembers={settings.addableMembers}
        isAdmin={isAdmin}
        onMemberAdd={settings.addMember}
        onMemberRoleChange={settings.changeMemberRole}
        onMemberRemove={settings.removeMember}
      />

      {isAdmin ? (
        <InvitationLinkPanel
          links={settings.invitations}
          onInvitationCreate={settings.createInvitation}
          onInvitationRevoke={settings.revokeInvitation}
        />
      ) : null}

      <BaseModal
        isOpen={isConfirmingDelete}
        title="Delete Board"
        onClose={() => setIsConfirmingDelete(false)}
      >
        <p className="mb-4 text-sm text-gray-700">
          Delete this Board and everything on it? This cannot be undone.
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
    </main>
  );
}

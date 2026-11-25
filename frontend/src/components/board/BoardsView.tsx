"use client";

import Link from "next/link";
import { useState } from "react";
import CreateBoardForm from "@/components/board/CreateBoardForm";
import BaseButton from "@/components/shared/BaseButton";
import BaseEmptyState from "@/components/shared/BaseEmptyState";
import BaseErrorState from "@/components/shared/BaseErrorState";
import BaseLoadingState from "@/components/shared/BaseLoadingState";
import useBoards from "@/hooks/useBoards";
import useTeams from "@/hooks/useTeams";

export default function BoardsView() {
  const [isArchived, setIsArchived] = useState<boolean>(false);
  const { boards, isLoading, error, reload, createBoard } =
    useBoards(isArchived);
  const { teams } = useTeams();

  return (
    <main className="flex flex-col gap-4 p-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Boards</h1>
        <BaseButton
          variant="secondary"
          aria-pressed={isArchived}
          onClick={() => setIsArchived((current) => !current)}
        >
          {isArchived ? "Show active Boards" : "Show archived Boards"}
        </BaseButton>
      </div>
      {isArchived ? null : (
        <CreateBoardForm teams={teams} onBoardCreate={createBoard} />
      )}
      {isLoading ? (
        <BaseLoadingState />
      ) : error ? (
        <BaseErrorState message={error} onRetry={reload} />
      ) : boards.length === 0 ? (
        <BaseEmptyState
          message={
            isArchived
              ? "No archived Boards."
              : "No Boards yet. Create one above."
          }
        />
      ) : (
        <ul className="divide-y divide-gray-200 rounded-lg border border-gray-200 bg-white">
          {boards.map((board) => (
            <li
              key={board.id}
              className="flex items-center justify-between gap-2 px-4 py-3 text-sm"
            >
              <Link
                href={`/boards/${board.id}`}
                className="font-medium text-gray-900 hover:underline"
              >
                {board.name}
              </Link>
              <span className="flex items-center gap-3 text-gray-600">
                <span>
                  {board.currentUserRole === "admin" ? "Admin" : "Member"}
                </span>
                <Link
                  href={`/boards/${board.id}/settings`}
                  className="text-blue-600 hover:underline"
                >
                  Settings
                </Link>
              </span>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}

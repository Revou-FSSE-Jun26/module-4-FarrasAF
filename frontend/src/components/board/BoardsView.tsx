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
    <main className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-4 lg:p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-slate-900">
            Boards
          </h1>
          <p className="mt-0.5 text-sm text-slate-500">
            {isArchived
              ? "Archived boards across your teams"
              : "Select a board or create a new one"}
          </p>
        </div>
        <BaseButton
          variant="secondary"
          aria-pressed={isArchived}
          onClick={() => setIsArchived((current) => !current)}
        >
          {isArchived ? "Show active Boards" : "Show archived Boards"}
        </BaseButton>
      </div>
      {isArchived ? null : (
        <div className="rounded-xl border border-slate-200/80 bg-white p-4 shadow-2xs">
          <CreateBoardForm teams={teams} onBoardCreate={createBoard} />
        </div>
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
        <ul className="divide-y divide-slate-100 overflow-hidden rounded-xl border border-slate-200/80 bg-white shadow-2xs">
          {boards.map((board) => (
            <li
              key={board.id}
              className="flex items-center justify-between gap-3 px-4 py-3.5 text-sm transition-colors hover:bg-slate-50/80"
            >
              <Link
                href={`/boards/${board.id}`}
                className="font-medium text-slate-900 hover:text-indigo-700"
              >
                {board.name}
              </Link>
              <span className="flex items-center gap-3 text-slate-500">
                <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
                  {board.currentUserRole === "admin" ? "Admin" : "Member"}
                </span>
                <Link
                  href={`/boards/${board.id}/settings`}
                  className="text-xs font-medium text-indigo-600 hover:text-indigo-700 hover:underline"
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

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
    <main className="rt-page">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="rt-kicker mb-3">Your command center</p>
          <h1 className="text-4xl font-bold tracking-tight text-slate-900">
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
        <div className="rt-panel p-5">
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
        <ul className="grid gap-4 sm:grid-cols-2">
          {boards.map((board) => (
            <li
              key={board.id}
              className="group relative flex min-h-40 flex-col justify-between overflow-hidden rounded-2xl border-[1.5px] border-[#211621] bg-[#fffdf7] p-5 text-sm shadow-[4px_4px_0_#211621] transition hover:-translate-y-1 hover:shadow-[7px_7px_0_#211621]"
            >
              <span aria-hidden="true" className="absolute -right-6 -top-6 size-20 rotate-12 rounded-2xl bg-[#c9b7ef] transition-transform group-hover:rotate-45" />
              <Link
                href={`/boards/${board.id}`}
                className="relative z-10 text-xl font-bold text-slate-900 after:absolute after:inset-0"
              >
                {board.name}
              </Link>
              <span className="relative z-20 flex items-center justify-between gap-3 text-slate-500">
                <span className="rounded-full border border-[#211621] bg-[#d9ff43] px-2.5 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-wider text-[#211621]">
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

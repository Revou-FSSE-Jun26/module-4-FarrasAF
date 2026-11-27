"use client";

import ChecklistProgress from "@/components/card/ChecklistProgress";
import BaseEmptyState from "@/components/shared/BaseEmptyState";
import BaseErrorState from "@/components/shared/BaseErrorState";
import BaseLoadingState from "@/components/shared/BaseLoadingState";
import BaseModal from "@/components/shared/BaseModal";
import { buildCommentTree } from "@/lib/comments";
import type { CommentNode } from "@/lib/comments";
import { useGuestBoard } from "@/hooks/useGuestBoard";
import type { GuestBoard, GuestCard, GuestComment } from "@/types/api";

interface GuestBoardViewProps {
  token: string;
}

const MENTION_PATTERN = /@\[([^\]]+)\]/g;

function renderGuestMentions(body: string, comments: GuestComment[]): string {
  const names = new Map<string, string>();
  for (const c of comments) names.set(c.author.id, c.author.displayName);
  return body.replace(
    MENTION_PATTERN,
    (_m, userId: string) => `@${names.get(userId) ?? "unknown"}`,
  );
}

function GuestCommentList({
  nodes,
  all,
}: {
  nodes: CommentNode<GuestComment>[];
  all: GuestComment[];
}) {
  return (
    <ul className="flex flex-col gap-2">
      {nodes.map(({ comment, replies }) => (
        <li key={comment.id} className="flex flex-col gap-2">
          <div className="rounded-md border border-gray-200 p-2">
            <p className="text-xs text-gray-600">
              {comment.author.displayName} ·{" "}
              {new Date(comment.createdAt).toLocaleString()}
              {comment.editedAt ? " (edited)" : ""}
            </p>
            <p className="text-sm break-words whitespace-pre-wrap text-gray-900">
              {renderGuestMentions(comment.body, all)}
            </p>
          </div>
          {replies.length > 0 ? (
            <div className="ml-4 border-l border-gray-200 pl-2">
              <GuestCommentList nodes={replies} all={all} />
            </div>
          ) : null}
        </li>
      ))}
    </ul>
  );
}

function GuestBoardColumns({
  board,
  onCardOpenEvent,
}: {
  board: GuestBoard;
  onCardOpenEvent: (cardId: string) => void;
}) {
  return (
    <div className="flex flex-col gap-4 lg:flex-row lg:items-start">
      {board.columns.map((column) => (
        <section
          key={column.id}
          aria-label={column.name}
          className="flex w-full flex-col gap-3 rounded-xl border border-slate-200/70 bg-slate-100/80 p-3 lg:min-w-0 lg:flex-1"
        >
          <div className="flex items-center justify-between gap-2 px-1">
            <h2 className="text-[13px] font-semibold tracking-tight text-slate-800">
              {column.name}
            </h2>
            <span className="rounded-full bg-slate-200/80 px-2 py-0.5 text-[11px] font-medium text-slate-600 tabular-nums">
              {column.cards.length}
            </span>
          </div>
          {column.cards.length === 0 ? (
            <p className="rounded-lg border border-dashed border-slate-200/90 px-3 py-4 text-center text-xs text-slate-400">
              No cards yet
            </p>
          ) : (
            <ul className="kanban-scroll flex flex-col gap-2 lg:max-h-[calc(100vh-14rem)] lg:overflow-y-auto lg:pr-0.5">
              {column.cards.map((card) => (
                <li key={card.id}>
                  <button
                    type="button"
                    onClick={() => onCardOpenEvent(card.id)}
                    className="w-full rounded-lg border border-slate-200/90 bg-white p-3 text-left text-sm text-slate-900 shadow-2xs transition duration-150 hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-sm"
                  >
                    <span className="block text-[13.5px] leading-snug font-medium break-words">
                      {card.title}
                    </span>
                    {card.dueDate ||
                    card.description.trim() ||
                    card.assignee ? (
                      <span className="mt-2 flex flex-wrap items-center gap-1.5 text-[11px] text-slate-500">
                        {card.dueDate ? (
                          <span className="inline-flex items-center gap-1 rounded-md bg-slate-100 px-1.5 py-0.5 font-medium text-slate-600 tabular-nums">
                            Due {card.dueDate}
                          </span>
                        ) : null}
                        {card.assignee ? (
                          <span className="inline-flex items-center rounded-md bg-indigo-50 px-1.5 py-0.5 font-medium text-indigo-700">
                            {card.assignee.displayName}
                          </span>
                        ) : null}
                      </span>
                    ) : null}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      ))}
    </div>
  );
}

function findCard(board: GuestBoard, cardId: string | null): GuestCard | null {
  if (cardId === null) return null;
  for (const column of board.columns) {
    const card = column.cards.find((c) => c.id === cardId);
    if (card) return card;
  }
  return null;
}

export default function GuestBoardView({ token }: GuestBoardViewProps) {
  const {
    status,
    board,
    comments,
    isCommentsLoading,
    hasCommentsError,
    selectedCardId,
    selectCardEvent,
    reload,
  } = useGuestBoard(token);

  if (status === "loading")
    return <BaseLoadingState label="Loading board..." />;
  if (status === "unavailable") {
    return <BaseErrorState message="This link is not available." />;
  }
  if (status === "error" || board === null) {
    return (
      <BaseErrorState message="Could not load the board." onRetry={reload} />
    );
  }

  const card = findCard(board, selectedCardId);

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-4 p-4">
      <header>
        <h1 className="text-xl font-semibold text-gray-900">{board.name}</h1>
        {board.description ? (
          <p className="text-sm break-words text-gray-600">
            {board.description}
          </p>
        ) : null}
        <p className="mt-1 text-xs text-gray-600">Read-only guest view</p>
      </header>
      {board.columns.length === 0 ? (
        <BaseEmptyState message="This board has no columns yet." />
      ) : (
        <GuestBoardColumns board={board} onCardOpenEvent={selectCardEvent} />
      )}
      <BaseModal
        isOpen={card !== null}
        title={card?.title ?? ""}
        onClose={() => selectCardEvent(null)}
      >
        {card ? (
          <div className="flex flex-col gap-3">
            {card.description ? (
              <p className="text-sm break-words whitespace-pre-wrap text-gray-900">
                {card.description}
              </p>
            ) : null}
            <p className="text-xs text-gray-600">
              Assignee: {card.assignee ? card.assignee.displayName : "None"}
              {card.dueDate ? ` · Due ${card.dueDate}` : ""}
            </p>
            {card.checklistItems.length > 0 ? (
              <section aria-label="To-do list" className="flex flex-col gap-2">
                <h3 className="text-sm font-semibold text-gray-900">
                  To-do list
                </h3>
                <ChecklistProgress items={card.checklistItems} />
                <ul className="flex flex-col gap-1.5">
                  {card.checklistItems.map((item) => (
                    <li key={item.id} className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={item.isDone}
                        disabled
                        aria-label={item.text}
                        className="size-4 shrink-0 accent-indigo-600"
                      />
                      <span
                        className={`text-sm break-words ${
                          item.isDone
                            ? "text-slate-400 line-through"
                            : "text-slate-900"
                        }`}
                      >
                        {item.text}
                      </span>
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}
            <h3 className="text-sm font-semibold text-gray-900">Comments</h3>
            {isCommentsLoading ? (
              <BaseLoadingState label="Loading comments..." />
            ) : hasCommentsError ? (
              <BaseErrorState message="Could not load comments." />
            ) : comments.length === 0 ? (
              <BaseEmptyState message="No comments yet" />
            ) : (
              <GuestCommentList
                nodes={buildCommentTree(comments)}
                all={comments}
              />
            )}
          </div>
        ) : null}
      </BaseModal>
    </div>
  );
}

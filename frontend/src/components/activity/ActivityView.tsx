"use client";

import Link from "next/link";
import BaseButton from "@/components/shared/BaseButton";
import BaseEmptyState from "@/components/shared/BaseEmptyState";
import BaseErrorState from "@/components/shared/BaseErrorState";
import BaseLoadingState from "@/components/shared/BaseLoadingState";
import useActivity from "@/hooks/useActivity";
import { describeActivity } from "@/lib/activityText";

interface ActivityViewProps {
  boardId: string;
}

function formatTime(iso: string): string {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : date.toLocaleString();
}

export default function ActivityView({ boardId }: ActivityViewProps) {
  const {
    activity,
    page,
    isLoading,
    error,
    hasPreviousPage,
    hasNextPage,
    reload,
    goToPreviousPage,
    goToNextPage,
  } = useActivity(boardId);

  return (
    <main className="flex flex-col gap-4 p-4">
      <div className="flex flex-col gap-1">
        <Link
          href={`/boards/${boardId}`}
          className="text-sm text-blue-600 hover:underline"
        >
          Back to Board
        </Link>
        <h1 className="text-xl font-semibold text-gray-900">Activity</h1>
      </div>

      {isLoading ? <BaseLoadingState /> : null}
      {!isLoading && error ? (
        <BaseErrorState message={error} onRetry={reload} />
      ) : null}
      {!isLoading && !error && activity ? (
        activity.items.length === 0 ? (
          <BaseEmptyState
            message={
              page === 0 ? "No activity yet." : "No activity on this page."
            }
            action={
              hasPreviousPage ? (
                <BaseButton variant="secondary" onClick={goToPreviousPage}>
                  Previous page
                </BaseButton>
              ) : undefined
            }
          />
        ) : (
          <>
            <ul className="flex flex-col gap-2">
              {activity.items.map((entry) => (
                <li
                  key={entry.id}
                  className="flex flex-col gap-1 rounded-md border border-gray-200 bg-white p-3 text-sm lg:flex-row lg:justify-between"
                >
                  <span className="break-words text-gray-900">
                    {describeActivity(entry)}
                  </span>
                  <time dateTime={entry.createdAt} className="text-gray-600">
                    {formatTime(entry.createdAt)}
                  </time>
                </li>
              ))}
            </ul>
            <nav
              aria-label="Activity pages"
              className="flex items-center gap-3"
            >
              <BaseButton
                variant="secondary"
                disabled={!hasPreviousPage}
                onClick={goToPreviousPage}
              >
                Previous page
              </BaseButton>
              <span className="text-sm text-gray-700">Page {page + 1}</span>
              <BaseButton
                variant="secondary"
                disabled={!hasNextPage}
                onClick={goToNextPage}
              >
                Next page
              </BaseButton>
            </nav>
          </>
        )
      ) : null}
    </main>
  );
}

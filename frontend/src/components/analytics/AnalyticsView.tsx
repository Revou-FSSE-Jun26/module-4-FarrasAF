"use client";

import Link from "next/link";
import BaseEmptyState from "@/components/shared/BaseEmptyState";
import BaseErrorState from "@/components/shared/BaseErrorState";
import BaseLoadingState from "@/components/shared/BaseLoadingState";
import useAnalytics from "@/hooks/useAnalytics";

interface AnalyticsViewProps {
  boardId: string;
}

export default function AnalyticsView({ boardId }: AnalyticsViewProps) {
  const { analytics, columnNames, isLoading, error, reload } =
    useAnalytics(boardId);

  return (
    <main className="rt-page max-w-5xl">
      <div className="flex flex-col gap-1">
        <Link
          href={`/boards/${boardId}`}
          className="text-sm text-blue-600 hover:underline"
        >
          Back to Board
        </Link>
        <p className="rt-kicker mt-3 mb-3">Momentum check</p>
        <h1 className="text-4xl font-bold text-gray-900">Analytics</h1>
      </div>

      {isLoading ? <BaseLoadingState /> : null}
      {!isLoading && error ? (
        <BaseErrorState message={error} onRetry={reload} />
      ) : null}
      {!isLoading && !error && analytics ? (
        <>
          <section
            aria-label="Summary"
            className="grid grid-cols-1 gap-3 lg:grid-cols-2"
          >
            <div className="rounded-2xl border-[1.5px] border-[#211621] bg-[#d9ff43] p-5 shadow-[4px_4px_0_#211621]">
              <p className="font-mono text-xs font-semibold uppercase tracking-wider text-gray-600">Total cards</p>
              <p className="mt-2 text-4xl font-bold text-gray-900">
                {analytics.totalCards}
              </p>
            </div>
            <div className="rounded-2xl border-[1.5px] border-[#211621] bg-[#ff7965] p-5 shadow-[4px_4px_0_#211621]">
              <p className="font-mono text-xs font-semibold uppercase tracking-wider text-gray-600">Completion rate</p>
              <p className="mt-2 text-4xl font-bold text-gray-900">
                {Math.round(analytics.completionRate * 100)}%
              </p>
            </div>
          </section>

          <section aria-labelledby="per-column-heading">
            <h2
              id="per-column-heading"
              className="mb-2 text-lg font-semibold text-gray-900"
            >
              Cards per Column
            </h2>
            {analytics.perColumn.length === 0 ? (
              <BaseEmptyState message="No Columns yet." />
            ) : (
              <ul className="flex flex-col gap-1">
                {analytics.perColumn.map((item) => (
                  <li
                    key={item.columnId}
                    className="flex justify-between rounded-md border border-gray-200 bg-white px-3 py-2 text-sm"
                  >
                    <span className="break-words text-gray-900">
                      {columnNames[item.columnId] ?? "Unknown column"}
                    </span>
                    <span className="text-gray-700">{item.count}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section aria-labelledby="by-day-heading">
            <h2
              id="by-day-heading"
              className="mb-2 text-lg font-semibold text-gray-900"
            >
              Activity by day (UTC)
            </h2>
            {analytics.activityByDay.length === 0 ? (
              <BaseEmptyState message="No activity yet." />
            ) : (
              <ul className="flex flex-col gap-1">
                {analytics.activityByDay.map((item) => (
                  <li
                    key={item.day}
                    className="flex justify-between rounded-md border border-gray-200 bg-white px-3 py-2 text-sm"
                  >
                    <span className="text-gray-900">{item.day}</span>
                    <span className="text-gray-700">{item.count}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      ) : null}
    </main>
  );
}

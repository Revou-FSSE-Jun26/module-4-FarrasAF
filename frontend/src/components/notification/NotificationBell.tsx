'use client';

import { useState } from 'react';
import NotificationItem from '@/components/notification/NotificationItem';
import BaseButton from '@/components/shared/BaseButton';
import BaseEmptyState from '@/components/shared/BaseEmptyState';
import BaseErrorState from '@/components/shared/BaseErrorState';
import BaseLoadingState from '@/components/shared/BaseLoadingState';
import useNotifications from '@/hooks/useNotifications';

export default function NotificationBell() {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const {
    items,
    unreadCount,
    isUnreadOnly,
    isLoading,
    isLoadingMore,
    hasMore,
    error,
    setUnreadOnly,
    loadMore,
    markRead,
    retry,
  } = useNotifications();

  return (
    <div className="relative">
      <BaseButton
        variant="secondary"
        size="sm"
        aria-label={`Notifications, ${unreadCount} unread`}
        aria-expanded={isOpen}
        onClick={() => setIsOpen((open) => !open)}
      >
        <svg
          aria-hidden="true"
          viewBox="0 0 20 20"
          fill="currentColor"
          className="size-4 text-slate-500"
        >
          <path
            fillRule="evenodd"
            d="M10 2a6 6 0 0 0-6 6c0 1.887-.454 3.665-1.257 5.234a.75.75 0 0 0 .515 1.076 32.91 32.91 0 0 0 3.256.508 3.5 3.5 0 0 0 6.972 0 32.903 32.903 0 0 0 3.256-.508.75.75 0 0 0 .515-1.076A11.448 11.448 0 0 1 16 8a6 6 0 0 0-6-6ZM8.05 14.943a33.54 33.54 0 0 0 3.9 0 2 2 0 0 1-3.9 0Z"
            clipRule="evenodd"
          />
        </svg>
        Notifications
        {unreadCount > 0 ? (
          <span className="rounded-full bg-rose-600 px-1.5 py-0.5 text-[11px] leading-none font-semibold text-white tabular-nums">
            {unreadCount}
          </span>
        ) : null}
      </BaseButton>
      {isOpen ? (
        <div className="absolute right-0 z-20 mt-2 w-80 max-w-[calc(100vw-2rem)] overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl ring-1 ring-slate-900/5">
          <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50/70 px-3.5 py-2.5">
            <label className="flex items-center gap-2 text-xs font-medium text-slate-700">
              <input
                type="checkbox"
                checked={isUnreadOnly}
                onChange={(e) => setUnreadOnly(e.target.checked)}
                className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
              />
              Unread only
            </label>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {isLoading ? (
              <BaseLoadingState label="Loading notifications..." />
            ) : error && items.length === 0 ? (
              <BaseErrorState message={error} onRetry={retry} />
            ) : items.length === 0 ? (
              <BaseEmptyState message="No notifications." />
            ) : (
              <>
                {error ? (
                  <p role="alert" className="px-3 py-2 text-xs text-red-600">
                    {error}
                  </p>
                ) : null}
                <ul>
                  {items.map((n) => (
                    <NotificationItem
                      key={n.id}
                      notification={n}
                      onMarkRead={(id) => void markRead(id)}
                    />
                  ))}
                </ul>
                {hasMore ? (
                  <div className="p-2 text-center">
                    <BaseButton
                      variant="secondary"
                      isLoading={isLoadingMore}
                      onClick={() => void loadMore()}
                    >
                      Load more
                    </BaseButton>
                  </div>
                ) : null}
              </>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}

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
        aria-label={`Notifications, ${unreadCount} unread`}
        aria-expanded={isOpen}
        onClick={() => setIsOpen((open) => !open)}
      >
        Notifications
        {unreadCount > 0 ? (
          <span className="rounded-full bg-red-600 px-2 text-xs text-white">
            {unreadCount}
          </span>
        ) : null}
      </BaseButton>
      {isOpen ? (
        <div className="absolute right-0 z-20 mt-2 w-80 max-w-[calc(100vw-2rem)] rounded-md border border-gray-200 bg-white shadow-lg">
          <div className="flex items-center justify-between border-b border-gray-200 px-3 py-2">
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={isUnreadOnly}
                onChange={(e) => setUnreadOnly(e.target.checked)}
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

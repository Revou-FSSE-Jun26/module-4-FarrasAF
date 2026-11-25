import Link from 'next/link';
import BaseButton from '@/components/shared/BaseButton';
import type { Notification } from '@/types/api';

interface NotificationItemProps {
  notification: Notification;
  onMarkRead: (notificationId: string) => void;
}

export default function NotificationItem({
  notification,
  onMarkRead,
}: NotificationItemProps) {
  const isUnread = notification.status === 'unread';
  return (
    <li
      className={`flex items-center justify-between gap-3 border-b border-gray-100 px-3 py-2 ${
        isUnread ? 'bg-blue-50' : ''
      }`}
    >
      <div className="min-w-0 text-sm">
        <Link
          href={`/boards/${encodeURIComponent(notification.boardId)}`}
          className="font-medium text-blue-700 hover:underline"
        >
          You were mentioned in a comment
        </Link>
        <p className="text-xs text-gray-500">
          {new Date(notification.createdAt).toLocaleString()}
        </p>
      </div>
      {isUnread ? (
        <BaseButton
          variant="secondary"
          className="min-h-8 px-2 py-1 text-xs"
          onClick={() => onMarkRead(notification.id)}
        >
          Mark as read
        </BaseButton>
      ) : null}
    </li>
  );
}

import Link from 'next/link';
import BaseButton from '@/components/shared/BaseButton';
import type { Notification } from '@/types/api';

interface NotificationItemProps {
  notification: Notification;
  onMarkRead: (notificationId: string) => void;
}

function notificationText(notification: Notification): string {
  if (notification.type === 'card_assigned') {
    return `You were assigned to the card "${notification.cardTitle ?? 'Untitled'}" in ${notification.boardName}`;
  }
  if (notification.cardTitle) {
    return `You were mentioned in a comment on the card "${notification.cardTitle}"`;
  }
  return 'You were mentioned in a comment';
}

export default function NotificationItem({
  notification,
  onMarkRead,
}: NotificationItemProps) {
  const isUnread = notification.status === 'unread';
  return (
    <li
      className={`flex items-center justify-between gap-3 border-b border-slate-100 px-3.5 py-2.5 transition-colors last:border-b-0 ${
        isUnread ? 'bg-indigo-50/60' : 'hover:bg-slate-50'
      }`}
    >
      <div className="min-w-0 text-sm">
        <Link
          href={`/boards/${encodeURIComponent(notification.boardId)}`}
          className="font-medium text-indigo-700 hover:underline"
        >
          {notificationText(notification)}
        </Link>
        <p className="mt-0.5 text-xs text-slate-500">
          {new Date(notification.createdAt).toLocaleString()}
        </p>
      </div>
      {isUnread ? (
        <BaseButton
          variant="secondary"
          size="sm"
          onClick={() => onMarkRead(notification.id)}
        >
          Mark as read
        </BaseButton>
      ) : null}
    </li>
  );
}

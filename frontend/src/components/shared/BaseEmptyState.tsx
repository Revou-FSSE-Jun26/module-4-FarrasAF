import type { ReactNode } from 'react';

interface BaseEmptyStateProps {
  message: string;
  action?: ReactNode;
}

export default function BaseEmptyState({
  message,
  action,
}: BaseEmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 p-6 text-center text-sm text-gray-600">
      <p>{message}</p>
      {action}
    </div>
  );
}

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
    <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-slate-200 bg-white/60 p-8 text-center text-sm text-slate-500">
      <p>{message}</p>
      {action}
    </div>
  );
}

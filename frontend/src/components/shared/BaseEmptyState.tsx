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
    <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border-[1.5px] border-dashed border-[#211621]/50 bg-[#fffdf7]/80 p-10 text-center text-sm text-slate-500">
      <span aria-hidden="true" className="mb-1 flex size-10 rotate-6 items-center justify-center rounded-xl border border-[#211621] bg-[#c9b7ef] font-mono text-lg font-bold text-[#211621]">·</span>
      <p>{message}</p>
      {action}
    </div>
  );
}

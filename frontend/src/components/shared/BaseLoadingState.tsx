interface BaseLoadingStateProps {
  label?: string;
}

export default function BaseLoadingState({
  label = 'Loading...',
}: BaseLoadingStateProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex items-center justify-center gap-2.5 p-8 text-sm text-slate-500"
    >
      <span
        aria-hidden="true"
        className="size-4 animate-spin rounded-full border-2 border-slate-200 border-t-indigo-600"
      />
      <span>{label}</span>
    </div>
  );
}

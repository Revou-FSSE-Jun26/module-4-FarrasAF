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
      className="flex items-center justify-center gap-2 p-6 text-sm text-gray-600"
    >
      <span
        aria-hidden="true"
        className="size-4 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600"
      />
      <span>{label}</span>
    </div>
  );
}

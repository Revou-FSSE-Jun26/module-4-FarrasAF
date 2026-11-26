import BaseButton from '@/components/shared/BaseButton';

interface BaseErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export default function BaseErrorState({
  message,
  onRetry,
}: BaseErrorStateProps) {
  return (
    <div
      role="alert"
      className="flex flex-col items-center justify-center gap-3 rounded-xl border border-rose-200 bg-rose-50/60 p-6 text-center text-sm text-rose-700"
    >
      <p>{message}</p>
      {onRetry ? (
        <BaseButton variant="secondary" onClick={onRetry}>
          Try again
        </BaseButton>
      ) : null}
    </div>
  );
}

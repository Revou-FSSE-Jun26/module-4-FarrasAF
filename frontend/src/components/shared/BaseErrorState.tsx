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
      className="flex flex-col items-center justify-center gap-3 rounded-2xl border-[1.5px] border-[#211621] bg-[#ff7965]/35 p-6 text-center text-sm text-[#6f2828] shadow-[3px_3px_0_#211621]"
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

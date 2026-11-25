'use client';

import BaseErrorFallback from '@/components/shared/BaseErrorFallback';

interface ErrorPageProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function ErrorPage({ error, reset }: ErrorPageProps) {
  return <BaseErrorFallback error={error} onRetry={reset} />;
}

'use client';

import BaseErrorFallback from '@/components/shared/BaseErrorFallback';

interface AppErrorPageProps {
  error: Error & { digest?: string };
  reset: () => void;
}

// Sits inside the (app) layout, so the navigation bar stays visible.
export default function AppErrorPage({ error, reset }: AppErrorPageProps) {
  return <BaseErrorFallback error={error} onRetry={reset} />;
}

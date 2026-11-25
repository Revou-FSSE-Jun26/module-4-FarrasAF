'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import BaseButton from '@/components/shared/BaseButton';
import { GENERIC_ERROR_MESSAGE, logError } from '@/lib/errorHandler';

interface BaseErrorFallbackProps {
  /** The caught error. Logged to the console in development only, never shown. */
  error?: Error;
  title?: string;
  message?: string;
  onRetry?: () => void;
}

/** Full-page fallback for error boundaries and not-found pages. */
export default function BaseErrorFallback({
  error,
  title = 'Something went wrong',
  message = GENERIC_ERROR_MESSAGE,
  onRetry,
}: BaseErrorFallbackProps) {
  useEffect(() => {
    if (error) logError(error, 'error-boundary');
  }, [error]);

  return (
    <main
      role="alert"
      className="flex flex-1 flex-col items-center justify-center gap-4 p-6 text-center"
    >
      <h1 className="text-xl font-semibold text-gray-900">{title}</h1>
      <p className="text-sm text-gray-600">{message}</p>
      <div className="flex items-center gap-3">
        {onRetry ? <BaseButton onClick={onRetry}>Try again</BaseButton> : null}
        <Link
          href="/"
          className="inline-flex min-h-10 items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-900 hover:bg-gray-100"
        >
          Go to home
        </Link>
      </div>
    </main>
  );
}

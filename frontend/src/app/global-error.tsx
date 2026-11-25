'use client';

import { useEffect } from 'react';
import { GENERIC_ERROR_MESSAGE, logError } from '@/lib/errorHandler';

interface GlobalErrorPageProps {
  error: Error & { digest?: string };
  reset: () => void;
}

// Replaces the root layout when it fails, so it renders its own <html> and
// <body>. Inline styles are used because the app stylesheet may not be loaded.
export default function GlobalErrorPage({
  error,
  reset,
}: GlobalErrorPageProps) {
  useEffect(() => {
    logError(error, 'global-error');
  }, [error]);

  return (
    <html lang="en">
      <body
        style={{
          margin: 0,
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '16px',
          padding: '24px',
          textAlign: 'center',
          fontFamily: 'system-ui, sans-serif',
        }}
      >
        <main role="alert">
          <h1 style={{ fontSize: '20px', margin: '0 0 8px' }}>
            Something went wrong
          </h1>
          <p style={{ fontSize: '14px', color: '#4b5563', margin: '0 0 16px' }}>
            {GENERIC_ERROR_MESSAGE}
          </p>
          <button
            type="button"
            onClick={reset}
            style={{
              minHeight: '40px',
              padding: '8px 16px',
              border: 'none',
              borderRadius: '6px',
              background: '#2563eb',
              color: '#ffffff',
              fontSize: '14px',
              cursor: 'pointer',
            }}
          >
            Try again
          </button>
        </main>
      </body>
    </html>
  );
}

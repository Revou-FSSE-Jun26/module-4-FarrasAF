'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import BaseToast from '@/components/shared/BaseToast';
import type { BaseToastVariant } from '@/components/shared/BaseToast';
import { ToastContext } from '@/hooks/useToast';
import type { ToastContextValue } from '@/hooks/useToast';
import { getErrorMessage, logError } from '@/lib/errorHandler';

const MAX_TOASTS = 3;

interface ToastItem {
  id: number;
  message: string;
  variant: BaseToastVariant;
}

interface BaseToastProviderProps {
  children: ReactNode;
}

export default function BaseToastProvider({
  children,
}: BaseToastProviderProps) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const nextId = useRef<number>(0);

  const dismiss = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const showToast = useCallback(
    (message: string, variant: BaseToastVariant = 'info') => {
      nextId.current += 1;
      const id = nextId.current;
      setToasts((current) => {
        if (current.some((t) => t.message === message && t.variant === variant)) {
          return current;
        }
        return [...current, { id, message, variant }].slice(-MAX_TOASTS);
      });
    },
    [],
  );

  const showError = useCallback(
    (err: unknown, fallback?: string) => {
      logError(err);
      showToast(getErrorMessage(err, fallback), 'error');
    },
    [showToast],
  );

  // Safety net for errors that no boundary or catch block sees: rejected
  // promises and errors thrown from event handlers.
  useEffect(() => {
    function handleRejection(event: PromiseRejectionEvent) {
      logError(event.reason, 'unhandledrejection');
      showToast(getErrorMessage(event.reason), 'error');
    }
    function handleError(event: ErrorEvent) {
      // Ignore opaque browser errors (e.g. ResizeObserver loop notices).
      if (!(event.error instanceof Error)) return;
      logError(event.error, 'window.error');
      showToast(getErrorMessage(event.error), 'error');
    }
    window.addEventListener('unhandledrejection', handleRejection);
    window.addEventListener('error', handleError);
    return () => {
      window.removeEventListener('unhandledrejection', handleRejection);
      window.removeEventListener('error', handleError);
    };
  }, [showToast]);

  const value = useMemo<ToastContextValue>(
    () => ({ showToast, showError }),
    [showToast, showError],
  );

  return (
    <ToastContext.Provider value={value}>
      {children}
      {toasts.length > 0 ? (
        <div className="fixed inset-x-4 bottom-4 z-50 flex flex-col gap-2 lg:inset-x-auto lg:right-4 lg:w-full lg:max-w-sm">
          {toasts.map((toast) => (
            <BaseToast
              key={toast.id}
              message={toast.message}
              variant={toast.variant}
              onDismiss={() => dismiss(toast.id)}
            />
          ))}
        </div>
      ) : null}
    </ToastContext.Provider>
  );
}

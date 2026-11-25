'use client';

import { useEffect, useRef } from 'react';

export type BaseToastVariant = 'success' | 'error' | 'info';

interface BaseToastProps {
  message: string;
  variant?: BaseToastVariant;
  durationMs?: number;
  onDismiss: () => void;
}

const VARIANT_CLASSES: Record<BaseToastVariant, string> = {
  success: 'bg-green-600 text-white',
  error: 'bg-red-600 text-white',
  info: 'bg-gray-900 text-white',
};

/** A single toast. Position it through its container (see BaseToastProvider). */
export default function BaseToast({
  message,
  variant = 'info',
  durationMs = 5000,
  onDismiss,
}: BaseToastProps) {
  // Keep the latest callback without restarting the dismiss timer.
  const onDismissRef = useRef<() => void>(onDismiss);
  useEffect(() => {
    onDismissRef.current = onDismiss;
  });

  useEffect(() => {
    const timer = setTimeout(() => onDismissRef.current(), durationMs);
    return () => clearTimeout(timer);
  }, [durationMs]);

  return (
    <div
      role={variant === 'error' ? 'alert' : 'status'}
      className={`flex items-center justify-between gap-4 rounded-md px-4 py-3 text-sm shadow-lg ${VARIANT_CLASSES[variant]}`}
    >
      <span>{message}</span>
      <button
        type="button"
        aria-label="Dismiss"
        onClick={onDismiss}
        className="min-h-8 min-w-8 rounded"
      >
        ×
      </button>
    </div>
  );
}

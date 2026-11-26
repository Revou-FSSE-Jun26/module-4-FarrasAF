'use client';

import { useId } from 'react';
import type { InputHTMLAttributes } from 'react';

interface BaseInputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export default function BaseInput({
  label,
  error,
  id,
  className = '',
  ...rest
}: BaseInputProps) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  const errorId = `${inputId}-error`;

  return (
    <div className="flex w-full flex-col gap-1.5">
      <label htmlFor={inputId} className="text-sm font-medium text-slate-700">
        {label}
      </label>
      <input
        id={inputId}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        className={`min-h-10 w-full rounded-lg border bg-white px-3 py-2 text-sm text-slate-900 shadow-2xs transition-colors placeholder:text-slate-400 focus:outline-none focus-visible:border-indigo-500 focus-visible:ring-2 focus-visible:ring-indigo-500/25 ${
          error ? 'border-rose-500' : 'border-slate-200 hover:border-slate-300'
        } ${className}`}
        {...rest}
      />
      {error ? (
        <p id={errorId} role="alert" className="text-xs font-medium text-rose-600">
          {error}
        </p>
      ) : null}
    </div>
  );
}

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
      <label htmlFor={inputId} className="font-mono text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-700">
        {label}
      </label>
      <input
        id={inputId}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        className={`min-h-11 w-full rounded-lg border-[1.5px] bg-[#fffdf7] px-3.5 py-2 text-sm text-slate-900 shadow-none transition-colors placeholder:text-slate-400 focus:outline-none focus-visible:border-[#3f2548] focus-visible:ring-2 focus-visible:ring-[#c9b7ef] ${
          error ? 'border-rose-500' : 'border-[#211621]/35 hover:border-[#211621]'
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

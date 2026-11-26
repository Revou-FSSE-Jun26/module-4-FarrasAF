import type { ButtonHTMLAttributes } from 'react';

type BaseButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost';
type BaseButtonSize = 'md' | 'sm';

interface BaseButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: BaseButtonVariant;
  size?: BaseButtonSize;
  isLoading?: boolean;
}

const VARIANT_CLASSES: Record<BaseButtonVariant, string> = {
  primary:
    'bg-indigo-600 text-white shadow-xs hover:bg-indigo-700 active:bg-indigo-800',
  secondary:
    'border border-slate-200 bg-white text-slate-700 shadow-2xs hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900',
  danger:
    'bg-rose-600 text-white shadow-xs hover:bg-rose-700 active:bg-rose-800',
  ghost:
    'bg-transparent text-slate-600 hover:bg-slate-200/70 hover:text-slate-900',
};

const SIZE_CLASSES: Record<BaseButtonSize, string> = {
  md: 'min-h-10 px-4 py-2 text-sm',
  sm: 'min-h-8 px-2.5 py-1 text-xs',
};

export default function BaseButton({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  disabled,
  type = 'button',
  className = '',
  children,
  ...rest
}: BaseButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled || isLoading}
      aria-busy={isLoading}
      className={`inline-flex items-center justify-center gap-1.5 rounded-lg font-medium transition-colors duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-50 ${SIZE_CLASSES[size]} ${VARIANT_CLASSES[variant]} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}

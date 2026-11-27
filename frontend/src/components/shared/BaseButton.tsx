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
    'border-[1.5px] border-[#211621] bg-[#d9ff43] text-[#211621] shadow-[3px_3px_0_#211621] hover:-translate-y-0.5 hover:shadow-[4px_4px_0_#211621] active:translate-y-0 active:shadow-[1px_1px_0_#211621]',
  secondary:
    'border-[1.5px] border-[#211621] bg-[#fffdf7] text-[#211621] shadow-[2px_2px_0_#211621] hover:bg-[#c9b7ef] hover:text-[#211621]',
  danger:
    'border-[1.5px] border-[#211621] bg-[#ff7965] text-[#211621] shadow-[3px_3px_0_#211621] hover:bg-[#ff927f]',
  ghost:
    'bg-transparent text-current hover:bg-[#d9ff43] hover:text-[#211621]',
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
      className={`inline-flex items-center justify-center gap-1.5 rounded-lg font-semibold transition duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#ff7965] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${SIZE_CLASSES[size]} ${VARIANT_CLASSES[variant]} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}

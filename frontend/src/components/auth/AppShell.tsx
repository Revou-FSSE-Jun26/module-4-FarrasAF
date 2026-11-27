'use client';

import type { ReactNode } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import NotificationBell from '@/components/notification/NotificationBell';
import BaseButton from '@/components/shared/BaseButton';
import BaseErrorState from '@/components/shared/BaseErrorState';
import BaseLoadingState from '@/components/shared/BaseLoadingState';
import useAuth from '@/hooks/useAuth';

interface AppShellProps {
  children: ReactNode;
}

const NAV_ITEMS: readonly { href: string; label: string }[] = [
  { href: '/teams', label: 'Teams' },
  { href: '/boards', label: 'Boards' },
  { href: '/search', label: 'Search' },
  { href: '/profile', label: 'Profile' },
];

export default function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const { user, isLoading, error, logout } = useAuth({ shouldLoadUser: true });

  if (isLoading) {
    return <BaseLoadingState />;
  }
  if (!user) {
    // On 401 apiClient redirects to /login; otherwise show the load error.
    return error ? (
      <BaseErrorState
        message={error}
        onRetry={() => window.location.reload()}
      />
    ) : (
      <BaseLoadingState />
    );
  }

  const initials = user.displayName
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('');

  return (
    <div className="flex min-h-full flex-1 flex-col">
      <header className="sticky top-0 z-30 flex flex-col gap-3 border-b-2 border-[#211621] bg-[#3f2548] px-4 py-3 text-[#f3eddc] shadow-[0_4px_0_#d9ff43] lg:flex-row lg:items-center lg:justify-between lg:px-6">
        <div className="flex flex-wrap items-center gap-3">
          <Link
            href="/boards"
            className="flex items-center gap-2 rounded-lg pr-1 text-sm font-bold tracking-tight text-[#f3eddc] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#d9ff43]"
          >
            <svg
              aria-hidden="true"
              viewBox="0 0 28 28"
              className="size-8 shrink-0 rotate-3 rounded-lg border border-[#211621]"
            >
              <defs>
                <linearGradient id="revotask-logo" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0" stopColor="#d9ff43" />
                  <stop offset="1" stopColor="#b8e61d" />
                </linearGradient>
              </defs>
              <rect width="28" height="28" rx="8" fill="url(#revotask-logo)" />
              <path
                d="M9.5 21V7h5.2a4.2 4.2 0 0 1 .9 8.3L19 21h-3.2l-3-5.4H12.5V21H9.5Zm3-8h2.1a1.6 1.6 0 0 0 0-3.2H12.5V13Z"
                fill="#211621"
                fillRule="evenodd"
              />
            </svg>
            <span className="hidden sm:inline">RevoTask</span>
          </Link>
          <span
            aria-hidden="true"
            className="hidden h-5 w-px bg-[#c9b7ef]/45 sm:inline-block"
          />
          <nav
            aria-label="Primary"
            className="flex flex-wrap items-center gap-1"
          >
            {NAV_ITEMS.map((item) => {
              const isActive =
                pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={isActive ? 'page' : undefined}
                  className={`rounded-full border px-3 py-1.5 text-sm font-semibold transition-colors ${
                    isActive
                      ? 'border-[#211621] bg-[#d9ff43] text-[#211621]'
                      : 'border-transparent text-[#e8dfca] hover:border-[#c9b7ef]/40 hover:bg-[#5b3866] hover:text-white'
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
        <div className="flex items-center justify-between gap-3 lg:justify-end">
          <NotificationBell />
          <div className="flex items-center gap-2 rounded-full border border-[#c9b7ef]/50 bg-[#2d1c33] py-1 pr-3 pl-1.5">
            <span
              aria-hidden="true"
              className="flex size-6 items-center justify-center rounded-full bg-[#ff7965] text-[11px] font-bold text-[#211621]"
            >
              {initials || '?'}
            </span>
            <span className="text-xs font-medium text-[#f3eddc]">
              {user.displayName}
            </span>
          </div>
          <BaseButton
            variant="ghost"
            size="sm"
            onClick={() => void logout()}
          >
            Log out
          </BaseButton>
        </div>
      </header>
      <div className="flex flex-1 flex-col">{children}</div>
    </div>
  );
}

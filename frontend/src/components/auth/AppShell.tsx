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
    <div className="flex min-h-full flex-1 flex-col bg-slate-50">
      <header className="sticky top-0 z-30 flex flex-col gap-2 border-b border-slate-200/80 bg-white/95 px-4 py-2.5 backdrop-blur-xs lg:flex-row lg:items-center lg:justify-between lg:px-6">
        <div className="flex flex-wrap items-center gap-3">
          <Link
            href="/boards"
            className="flex items-center gap-2 rounded-lg pr-1 text-sm font-semibold tracking-tight text-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
          >
            <span
              aria-hidden="true"
              className="flex size-7 items-center justify-center rounded-lg bg-indigo-600 text-xs font-bold text-white shadow-2xs"
            >
              K
            </span>
            <span className="hidden sm:inline">Kanban</span>
          </Link>
          <span
            aria-hidden="true"
            className="hidden h-4 w-px bg-slate-200 sm:inline-block"
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
                  className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-indigo-50 text-indigo-700'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
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
          <div className="flex items-center gap-2 rounded-full border border-slate-200/80 bg-slate-50 py-1 pr-3 pl-1.5">
            <span
              aria-hidden="true"
              className="flex size-6 items-center justify-center rounded-full bg-indigo-100 text-[11px] font-semibold text-indigo-700"
            >
              {initials || '?'}
            </span>
            <span className="text-xs font-medium text-slate-700">
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

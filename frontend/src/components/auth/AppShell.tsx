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

  return (
    <div className="flex min-h-full flex-1 flex-col">
      <header className="flex flex-col gap-2 border-b border-gray-200 bg-white px-4 py-2 lg:flex-row lg:items-center lg:justify-between">
        <nav aria-label="Primary" className="flex flex-wrap items-center gap-1">
          {NAV_ITEMS.map((item) => {
            const isActive =
              pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={isActive ? 'page' : undefined}
                className={`rounded-md px-3 py-2 text-sm font-medium ${
                  isActive
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="flex items-center gap-3">
          <NotificationBell />
          <span className="text-sm text-gray-700">{user.displayName}</span>
          <BaseButton variant="secondary" onClick={() => void logout()}>
            Log out
          </BaseButton>
        </div>
      </header>
      <div className="flex flex-1 flex-col">{children}</div>
    </div>
  );
}

import { Suspense } from "react";
import type { ReactNode } from "react";
import AppShell from "@/components/auth/AppShell";

export default function AuthenticatedLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <Suspense>
      <AppShell>{children}</AppShell>
    </Suspense>
  );
}

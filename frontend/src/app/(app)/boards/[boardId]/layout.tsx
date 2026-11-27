import type { ReactNode } from "react";
import BoardProvider from "@/components/board/BoardProvider";
import BoardShell from "@/components/board/BoardShell";

export default async function BoardLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: Promise<{ boardId: string }>;
}) {
  const { boardId } = await params;
  return (
    <BoardProvider boardId={boardId}>
      <BoardShell>{children}</BoardShell>
    </BoardProvider>
  );
}

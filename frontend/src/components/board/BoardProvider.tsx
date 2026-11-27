"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import useBoard from "@/hooks/useBoard";
import { BoardContext } from "@/hooks/useBoardContext";

interface BoardProviderProps {
  boardId: string;
  children: ReactNode;
}

export default function BoardProvider({
  boardId,
  children,
}: BoardProviderProps) {
  const boardState = useBoard(boardId);
  const [openCardId, setOpenCardId] = useState<string | null>(null);
  const pathname = usePathname();
  const previousPathname = useRef<string>(pathname);
  const { refreshBoard } = boardState;

  // Board pages share one fetch. Refetch silently when moving between them so
  // changes made on Board settings show up on the Board view.
  useEffect(() => {
    if (previousPathname.current === pathname) return;
    previousPathname.current = pathname;
    refreshBoard().catch(() => {
      // The Board may be gone (deleted in settings); the page shows its own state.
    });
  }, [pathname, refreshBoard]);

  return (
    <BoardContext.Provider
      value={{ ...boardState, boardId, openCardId, setOpenCardId }}
    >
      {children}
    </BoardContext.Provider>
  );
}

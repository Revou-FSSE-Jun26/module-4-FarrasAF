"use client";

import type { ReactNode } from "react";
import BoardSidebar from "@/components/board/BoardSidebar";
import CardDetailModal from "@/components/card/CardDetailModal";
import useBoardContext from "@/hooks/useBoardContext";

interface BoardShellProps {
  children: ReactNode;
}

export default function BoardShell({ children }: BoardShellProps) {
  const { board, refreshBoard, openCardId, setOpenCardId, currentUserId } =
    useBoardContext();
  const openCard =
    board?.columns
      .flatMap((column) => column.cards)
      .find((card) => card.id === openCardId) ?? null;

  return (
    <div className="flex flex-1 flex-col lg:flex-row">
      <BoardSidebar />
      <div className="flex min-w-0 flex-1 flex-col">{children}</div>
      {board && openCard ? (
        <CardDetailModal
          key={openCard.id}
          boardId={board.id}
          card={openCard}
          currentUserId={currentUserId}
          currentUserRole={board.currentUserRole}
          onCardChange={refreshBoard}
          onClose={() => setOpenCardId(null)}
        />
      ) : null}
    </div>
  );
}

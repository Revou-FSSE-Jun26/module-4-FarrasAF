"use client";

import { createContext, useContext } from "react";
import type { UseBoardResult } from "@/hooks/useBoard";

export interface BoardContextValue extends UseBoardResult {
  boardId: string;
  openCardId: string | null;
  setOpenCardId: (cardId: string | null) => void;
  currentUserId: string | null;
  isMyTasksOn: boolean;
  setIsMyTasksOn: (isOn: boolean) => void;
}

export const BoardContext = createContext<BoardContextValue | null>(null);

export default function useBoardContext(): BoardContextValue {
  const value = useContext(BoardContext);
  if (!value) {
    throw new Error("useBoardContext must be used inside BoardProvider.");
  }
  return value;
}

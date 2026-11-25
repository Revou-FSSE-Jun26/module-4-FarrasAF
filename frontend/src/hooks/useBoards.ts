"use client";

import { useCallback, useEffect, useState } from "react";
import useToast from "@/hooks/useToast";
import { apiClient } from "@/lib/apiClient";
import { getErrorMessage } from "@/lib/errorHandler";
import type {
  Board,
  BoardMember,
  BoardRole,
  InvitationLink,
  TeamMember,
  UpdateBoardRequest,
} from "@/types/api";

interface UseBoardsResult {
  boards: Board[];
  isLoading: boolean;
  error: string | null;
  reload: () => void;
  createBoard: (teamId: string, name: string) => Promise<Board>;
}

export default function useBoards(isArchived: boolean): UseBoardsResult {
  const { showError } = useToast();
  const [boards, setBoards] = useState<Board[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState<number>(0);

  useEffect(() => {
    let isActive = true;
    apiClient
      .listBoards({ archived: isArchived })
      .then((res) => {
        if (!isActive) return;
        setBoards(res.items);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!isActive) return;
        setError(getErrorMessage(err, "Could not load your Boards."));
        showError(err, "Could not load your Boards.");
      })
      .finally(() => {
        if (isActive) setIsLoading(false);
      });
    return () => {
      isActive = false;
    };
  }, [isArchived, reloadKey, showError]);

  const reload = useCallback(() => {
    setIsLoading(true);
    setReloadKey((key) => key + 1);
  }, []);

  const createBoard = useCallback(
    async (teamId: string, name: string): Promise<Board> => {
      const board = await apiClient.createBoard({ teamId, name });
      if (!isArchived) setBoards((current) => [...current, board]);
      return board;
    },
    [isArchived],
  );

  return { boards, isLoading, error, reload, createBoard };
}

interface UseBoardSettingsResult {
  board: Board | null;
  members: BoardMember[];
  addableMembers: TeamMember[];
  invitations: InvitationLink[];
  isLoading: boolean;
  error: string | null;
  reload: () => void;
  updateBoard: (body: UpdateBoardRequest) => Promise<boolean>;
  archiveBoard: () => Promise<boolean>;
  restoreBoard: () => Promise<boolean>;
  deleteBoard: () => Promise<boolean>;
  addMember: (userId: string, role: BoardRole) => Promise<void>;
  changeMemberRole: (userId: string, role: BoardRole) => Promise<void>;
  removeMember: (userId: string) => Promise<void>;
  createInvitation: () => Promise<void>;
  revokeInvitation: (token: string) => Promise<void>;
}

export function useBoardSettings(boardId: string): UseBoardSettingsResult {
  const { showError } = useToast();
  const [board, setBoard] = useState<Board | null>(null);
  const [members, setMembers] = useState<BoardMember[]>([]);
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [invitations, setInvitations] = useState<InvitationLink[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState<number>(0);

  useEffect(() => {
    let isActive = true;
    async function load(): Promise<void> {
      try {
        const [loadedBoard, memberList] = await Promise.all([
          apiClient.getBoard(boardId),
          apiClient.listBoardMembers(boardId),
        ]);
        // Admin-only data; the role comes from the Board response.
        const isAdmin = loadedBoard.currentUserRole === "admin";
        const [links, teamList] = isAdmin
          ? await Promise.all([
              apiClient.listInvitations(boardId),
              apiClient.listTeamMembers(loadedBoard.teamId),
            ])
          : [null, null];
        if (!isActive) return;
        setBoard(loadedBoard);
        setMembers(memberList.items);
        setInvitations(links ? links.items : []);
        setTeamMembers(teamList ? teamList.items : []);
        setError(null);
      } catch (err: unknown) {
        if (isActive) {
          setError(getErrorMessage(err, "Could not load this Board."));
          showError(err, "Could not load this Board.");
        }
      } finally {
        if (isActive) setIsLoading(false);
      }
    }
    void load();
    return () => {
      isActive = false;
    };
  }, [boardId, reloadKey, showError]);

  const reload = useCallback(() => {
    setIsLoading(true);
    setReloadKey((key) => key + 1);
  }, []);

  const run = useCallback(
    async (action: () => Promise<void>, fallback: string): Promise<boolean> => {
      try {
        await action();
        return true;
      } catch (err: unknown) {
        showError(err, fallback);
        return false;
      }
    },
    [showError],
  );

  const refetchMembers = useCallback(async (): Promise<void> => {
    // Roles are read from the server after membership changes.
    const [loadedBoard, memberList] = await Promise.all([
      apiClient.getBoard(boardId),
      apiClient.listBoardMembers(boardId),
    ]);
    setBoard(loadedBoard);
    setMembers(memberList.items);
  }, [boardId]);

  const updateBoard = useCallback(
    (body: UpdateBoardRequest) =>
      run(async () => {
        const updated = await apiClient.updateBoard(boardId, body);
        setBoard((current) => (current ? { ...current, ...updated } : updated));
      }, "Could not save the Board."),
    [boardId, run],
  );

  const archiveBoard = useCallback(
    () =>
      run(async () => {
        const updated = await apiClient.archiveBoard(boardId);
        setBoard((current) => (current ? { ...current, ...updated } : updated));
      }, "Could not archive the Board."),
    [boardId, run],
  );

  const restoreBoard = useCallback(
    () =>
      run(async () => {
        const updated = await apiClient.restoreBoard(boardId);
        setBoard((current) => (current ? { ...current, ...updated } : updated));
      }, "Could not restore the Board."),
    [boardId, run],
  );

  const deleteBoard = useCallback(
    () =>
      run(async () => {
        await apiClient.deleteBoard(boardId);
      }, "Could not delete the Board."),
    [boardId, run],
  );

  const addMember = useCallback(
    async (userId: string, role: BoardRole): Promise<void> => {
      await run(async () => {
        await apiClient.addBoardMember(boardId, { userId, role });
        await refetchMembers();
      }, "Could not add the member.");
    },
    [boardId, refetchMembers, run],
  );

  const changeMemberRole = useCallback(
    async (userId: string, role: BoardRole): Promise<void> => {
      await run(async () => {
        await apiClient.changeBoardMemberRole(boardId, userId, { role });
        await refetchMembers();
      }, "Could not change the role.");
    },
    [boardId, refetchMembers, run],
  );

  const removeMember = useCallback(
    async (userId: string): Promise<void> => {
      await run(async () => {
        await apiClient.removeBoardMember(boardId, userId);
        await refetchMembers();
      }, "Could not remove the member.");
    },
    [boardId, refetchMembers, run],
  );

  const createInvitation = useCallback(async (): Promise<void> => {
    await run(async () => {
      const link = await apiClient.createInvitation(boardId);
      setInvitations((current) => [link, ...current]);
    }, "Could not create the invitation link.");
  }, [boardId, run]);

  const revokeInvitation = useCallback(
    async (token: string): Promise<void> => {
      await run(async () => {
        const updated = await apiClient.revokeInvitation(token);
        setInvitations((current) =>
          current.map((link) => (link.token === token ? updated : link)),
        );
      }, "Could not revoke the invitation link.");
    },
    [run],
  );

  const memberIds = new Set(members.map((member) => member.userId));
  const addableMembers = teamMembers.filter(
    (member) => !memberIds.has(member.userId),
  );

  return {
    board,
    members,
    addableMembers,
    invitations,
    isLoading,
    error,
    reload,
    updateBoard,
    archiveBoard,
    restoreBoard,
    deleteBoard,
    addMember,
    changeMemberRole,
    removeMember,
    createInvitation,
    revokeInvitation,
  };
}

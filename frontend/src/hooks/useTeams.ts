"use client";

import { useCallback, useEffect, useState } from "react";
import useToast from "@/hooks/useToast";
import { ApiError, apiClient } from "@/lib/apiClient";
import { getErrorMessage } from "@/lib/errorHandler";
import type { Team, TeamJoinLink, TeamMember } from "@/types/api";

interface UseTeamsResult {
  teams: Team[];
  isLoading: boolean;
  error: string | null;
  reload: () => void;
  createTeam: (name: string) => Promise<Team>;
}

export default function useTeams(): UseTeamsResult {
  const { showError } = useToast();
  const [teams, setTeams] = useState<Team[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState<number>(0);

  useEffect(() => {
    let isActive = true;
    apiClient
      .listTeams()
      .then((res) => {
        if (!isActive) return;
        setTeams(res.items);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!isActive) return;
        setError(getErrorMessage(err, "Could not load your Teams."));
        showError(err, "Could not load your Teams.");
      })
      .finally(() => {
        if (isActive) setIsLoading(false);
      });
    return () => {
      isActive = false;
    };
  }, [reloadKey, showError]);

  const reload = useCallback(() => {
    setIsLoading(true);
    setReloadKey((key) => key + 1);
  }, []);

  const createTeam = useCallback(async (name: string): Promise<Team> => {
    const team = await apiClient.createTeam({ name });
    setTeams((current) => [...current, team]);
    return team;
  }, []);

  return { teams, isLoading, error, reload, createTeam };
}

interface UseTeamDetailResult {
  team: Team | null;
  members: TeamMember[];
  joinLinks: TeamJoinLink[];
  isLoading: boolean;
  error: string | null;
  reload: () => void;
  createJoinLink: () => Promise<void>;
  revokeJoinLink: (token: string) => Promise<void>;
}

export function useTeamDetail(teamId: string): UseTeamDetailResult {
  const { showError } = useToast();
  const [team, setTeam] = useState<Team | null>(null);
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [joinLinks, setJoinLinks] = useState<TeamJoinLink[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState<number>(0);

  useEffect(() => {
    let isActive = true;
    async function load(): Promise<void> {
      try {
        const [teamList, memberList] = await Promise.all([
          apiClient.listTeams(),
          apiClient.listTeamMembers(teamId),
        ]);
        const found = teamList.items.find((item) => item.id === teamId);
        if (!found) {
          throw new ApiError(404, {
            code: "not_found",
            message: "Team not found.",
          });
        }
        // Join links are Team_Admin only; the role comes from the Team response.
        const links =
          found.currentUserTeamRole === "team_admin"
            ? (await apiClient.listTeamJoinLinks(teamId)).items
            : [];
        if (!isActive) return;
        setTeam(found);
        setMembers(memberList.items);
        setJoinLinks(links);
        setError(null);
      } catch (err: unknown) {
        if (isActive) {
          setError(getErrorMessage(err, "Could not load this Team."));
          showError(err, "Could not load this Team.");
        }
      } finally {
        if (isActive) setIsLoading(false);
      }
    }
    void load();
    return () => {
      isActive = false;
    };
  }, [teamId, reloadKey, showError]);

  const reload = useCallback(() => {
    setIsLoading(true);
    setReloadKey((key) => key + 1);
  }, []);

  const createJoinLink = useCallback(async (): Promise<void> => {
    try {
      const link = await apiClient.createTeamJoinLink(teamId);
      setJoinLinks((current) => [link, ...current]);
    } catch (err: unknown) {
      showError(err, "Could not create the join link.");
    }
  }, [teamId, showError]);

  const revokeJoinLink = useCallback(
    async (token: string): Promise<void> => {
      try {
        const updated = await apiClient.revokeTeamJoinLink(token);
        setJoinLinks((current) =>
          current.map((link) => (link.token === token ? updated : link)),
        );
      } catch (err: unknown) {
        showError(err, "Could not revoke the join link.");
      }
    },
    [showError],
  );

  return {
    team,
    members,
    joinLinks,
    isLoading,
    error,
    reload,
    createJoinLink,
    revokeJoinLink,
  };
}

type JoinStatus = "loading" | "ready" | "invalid" | "joining";

interface UseJoinTeamResult {
  status: JoinStatus;
  teamName: string | null;
  confirmJoin: () => Promise<string | null>;
}

/** Preview a Team_Join_Link, then accept it only after the user confirms. */
export function useJoinTeam(token: string): UseJoinTeamResult {
  const [status, setStatus] = useState<JoinStatus>("loading");
  const [teamName, setTeamName] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;
    apiClient
      .previewTeamJoinLink(token)
      .then((preview) => {
        if (!isActive) return;
        setTeamName(preview.teamName);
        setStatus("ready");
      })
      .catch(() => {
        // One generic outcome for invalid, inactive, or expired links.
        if (isActive) setStatus("invalid");
      });
    return () => {
      isActive = false;
    };
  }, [token]);

  const confirmJoin = useCallback(async (): Promise<string | null> => {
    setStatus("joining");
    try {
      const res = await apiClient.acceptTeamJoinLink(token);
      return res.teamId;
    } catch {
      setStatus("invalid");
      return null;
    }
  }, [token]);

  return { status, teamName, confirmJoin };
}

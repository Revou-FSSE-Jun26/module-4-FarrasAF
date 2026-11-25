"use client";

import Link from "next/link";
import BaseEmptyState from "@/components/shared/BaseEmptyState";
import BaseErrorState from "@/components/shared/BaseErrorState";
import BaseLoadingState from "@/components/shared/BaseLoadingState";
import CreateTeamForm from "@/components/team/CreateTeamForm";
import useTeams from "@/hooks/useTeams";

export default function TeamsView() {
  const { teams, isLoading, error, reload, createTeam } = useTeams();

  return (
    <main className="flex flex-col gap-4 p-4">
      <h1 className="text-xl font-semibold text-gray-900">Teams</h1>
      <CreateTeamForm onTeamCreate={createTeam} />
      {isLoading ? (
        <BaseLoadingState />
      ) : error ? (
        <BaseErrorState message={error} onRetry={reload} />
      ) : teams.length === 0 ? (
        <BaseEmptyState message="You are not in any Team yet. Create one above." />
      ) : (
        <ul className="divide-y divide-gray-200 rounded-lg border border-gray-200 bg-white">
          {teams.map((team) => (
            <li key={team.id}>
              <Link
                href={`/teams/${team.id}`}
                className="flex items-center justify-between px-4 py-3 text-sm hover:bg-gray-50"
              >
                <span className="font-medium text-gray-900">{team.name}</span>
                <span className="text-gray-600">
                  {team.currentUserTeamRole === "team_admin"
                    ? "Team admin"
                    : "Member"}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}

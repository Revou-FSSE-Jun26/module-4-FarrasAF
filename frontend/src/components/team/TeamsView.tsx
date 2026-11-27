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
    <main className="rt-page">
      <div>
        <p className="rt-kicker mb-3">Better together</p>
        <h1 className="text-4xl font-bold text-gray-900">Teams</h1>
        <p className="mt-1 text-sm text-gray-600">The people and spaces moving work forward.</p>
      </div>
      <div className="rt-panel p-5"><CreateTeamForm onTeamCreate={createTeam} /></div>
      {isLoading ? (
        <BaseLoadingState />
      ) : error ? (
        <BaseErrorState message={error} onRetry={reload} />
      ) : teams.length === 0 ? (
        <BaseEmptyState message="You are not in any Team yet. Create one above." />
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2">
          {teams.map((team) => (
            <li key={team.id}>
              <Link
                href={`/teams/${team.id}`}
                className="flex min-h-32 flex-col items-start justify-between rounded-2xl border-[1.5px] border-[#211621] bg-[#fffdf7] p-5 text-sm shadow-[4px_4px_0_#211621] transition hover:-translate-y-1 hover:bg-[#c9b7ef]"
              >
                <span className="text-xl font-bold text-gray-900">{team.name}</span>
                <span className="rounded-full border border-[#211621] bg-[#f3eddc] px-2.5 py-1 font-mono text-[10px] font-semibold uppercase tracking-wider text-gray-600">
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

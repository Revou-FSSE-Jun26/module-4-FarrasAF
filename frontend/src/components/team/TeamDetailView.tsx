"use client";

import Link from "next/link";
import BaseErrorState from "@/components/shared/BaseErrorState";
import BaseLoadingState from "@/components/shared/BaseLoadingState";
import JoinLinkPanel from "@/components/team/JoinLinkPanel";
import TeamMemberList from "@/components/team/TeamMemberList";
import { useTeamDetail } from "@/hooks/useTeams";

interface TeamDetailViewProps {
  teamId: string;
}

export default function TeamDetailView({ teamId }: TeamDetailViewProps) {
  const {
    team,
    members,
    joinLinks,
    isLoading,
    error,
    reload,
    createJoinLink,
    revokeJoinLink,
  } = useTeamDetail(teamId);

  if (isLoading) return <BaseLoadingState />;
  if (error || !team) {
    return (
      <BaseErrorState
        message={error ?? "Could not load this Team."}
        onRetry={reload}
      />
    );
  }

  return (
    <main className="rt-page max-w-5xl">
      <div className="flex flex-col gap-1">
        <Link href="/teams" className="text-sm text-blue-600 hover:underline">
          Back to Teams
        </Link>
        <p className="rt-kicker mt-3 mb-3">Team space</p>
        <h1 className="text-4xl font-bold text-gray-900">{team.name}</h1>
      </div>
      <section
        aria-labelledby="members-heading"
        className="flex flex-col gap-3"
      >
        <h2 id="members-heading" className="text-lg font-semibold">
          Members
        </h2>
        <TeamMemberList members={members} />
      </section>
      {team.currentUserTeamRole === "team_admin" ? (
        <JoinLinkPanel
          links={joinLinks}
          onJoinLinkCreate={createJoinLink}
          onJoinLinkRevoke={revokeJoinLink}
        />
      ) : null}
    </main>
  );
}

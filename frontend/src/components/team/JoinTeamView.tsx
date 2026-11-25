"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import BaseButton from "@/components/shared/BaseButton";
import BaseLoadingState from "@/components/shared/BaseLoadingState";
import { useJoinTeam } from "@/hooks/useTeams";

interface JoinTeamViewProps {
  token: string;
}

export default function JoinTeamView({ token }: JoinTeamViewProps) {
  const router = useRouter();
  const { status, teamName, confirmJoin } = useJoinTeam(token);

  async function handleJoin() {
    const teamId = await confirmJoin();
    if (teamId) router.replace(`/teams/${teamId}`);
  }

  if (status === "loading") return <BaseLoadingState />;

  if (status === "invalid") {
    return (
      <main className="flex flex-1 items-center justify-center p-4">
        <div
          role="alert"
          className="flex max-w-sm flex-col gap-3 rounded-lg border border-gray-200 bg-white p-6 text-center"
        >
          <p className="text-sm text-gray-900">This join link is not valid.</p>
          <Link href="/teams" className="text-sm text-blue-600 hover:underline">
            Go to Teams
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="flex flex-1 items-center justify-center p-4">
      <div className="flex max-w-sm flex-col gap-4 rounded-lg border border-gray-200 bg-white p-6 text-center">
        <h1 className="text-xl font-semibold text-gray-900">
          Join {teamName}?
        </h1>
        <BaseButton
          isLoading={status === "joining"}
          onClick={() => void handleJoin()}
        >
          Join Team
        </BaseButton>
      </div>
    </main>
  );
}

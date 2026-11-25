import JoinTeamView from "@/components/team/JoinTeamView";

export default async function JoinPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;
  return <JoinTeamView token={token} />;
}

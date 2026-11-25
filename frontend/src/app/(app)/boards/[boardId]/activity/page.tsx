import ActivityView from "@/components/activity/ActivityView";

export default async function BoardActivityPage({
  params,
}: {
  params: Promise<{ boardId: string }>;
}) {
  const { boardId } = await params;
  return <ActivityView boardId={boardId} />;
}

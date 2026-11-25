import BoardSettingsView from "@/components/board/BoardSettingsView";

export default async function BoardSettingsPage({
  params,
}: {
  params: Promise<{ boardId: string }>;
}) {
  const { boardId } = await params;
  return <BoardSettingsView boardId={boardId} />;
}

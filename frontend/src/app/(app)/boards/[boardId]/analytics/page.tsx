import AnalyticsView from "@/components/analytics/AnalyticsView";

export default async function BoardAnalyticsPage({
  params,
}: {
  params: Promise<{ boardId: string }>;
}) {
  const { boardId } = await params;
  return <AnalyticsView boardId={boardId} />;
}

import type { BoardColumn } from "@/types/api";

// Same Columns, each holding only the Cards assigned to the given User.
export function filterColumnsByAssignee(
  columns: readonly BoardColumn[],
  userId: string,
): BoardColumn[] {
  return columns.map((column) => ({
    ...column,
    cards: column.cards.filter((card) => card.assigneeId === userId),
  }));
}

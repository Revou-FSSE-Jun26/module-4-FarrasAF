import type { BoardColumn, Card } from "@/types/api";

export interface CardSearchResult {
  card: Card;
  columnName: string;
}

// Cards of one Board whose Title contains the query as a case-insensitive
// substring. The query is trimmed; an empty query returns no results. Results
// follow Column order, then Card order.
export function filterCardsByTitle(
  columns: BoardColumn[],
  query: string,
): CardSearchResult[] {
  const needle = query.trim().toLowerCase();
  if (needle.length === 0) return [];
  return [...columns]
    .sort((a, b) => a.orderIndex - b.orderIndex)
    .flatMap((column) =>
      [...column.cards]
        .sort((a, b) => a.orderIndex - b.orderIndex)
        .filter((card) => card.title.toLowerCase().includes(needle))
        .map((card) => ({ card, columnName: column.name })),
    );
}

import type { BoardColumn, Card } from "@/types/api";

export interface DropTarget {
  cardId: string;
  targetColumnId: string;
  targetIndex: number;
}

function sortedCards(column: BoardColumn): Card[] {
  return [...column.cards].sort((a, b) => a.orderIndex - b.orderIndex);
}

// Computes where a dragged Card lands. `overId` is either a Column id (drop on
// the Column body, appends) or a Card id (drop on a Card, takes its place).
// Returns null when the drop is not a real move.
export function computeDropTarget(
  columns: BoardColumn[],
  activeId: string,
  overId: string | null,
): DropTarget | null {
  if (overId === null || overId === activeId) return null;

  const source = columns.find((c) =>
    c.cards.some((card) => card.id === activeId),
  );
  if (!source) return null;
  const sourceCards = sortedCards(source);
  const sourceIndex = sourceCards.findIndex((card) => card.id === activeId);

  const overColumn = columns.find((c) => c.id === overId);
  let targetColumn: BoardColumn;
  let targetIndex: number;

  if (overColumn) {
    targetColumn = overColumn;
    const remaining = sortedCards(overColumn).filter(
      (card) => card.id !== activeId,
    );
    targetIndex = remaining.length;
  } else {
    const found = columns.find((c) =>
      c.cards.some((card) => card.id === overId),
    );
    if (!found) return null;
    targetColumn = found;
    targetIndex = sortedCards(found).findIndex((card) => card.id === overId);
  }

  if (targetColumn.id === source.id && targetIndex === sourceIndex) return null;
  return { cardId: activeId, targetColumnId: targetColumn.id, targetIndex };
}

// Returns new Columns with the Card moved and orderIndex contiguous from 0.
export function applyMove(
  columns: BoardColumn[],
  target: DropTarget,
): BoardColumn[] {
  const moving = columns
    .flatMap((c) => c.cards)
    .find((card) => card.id === target.cardId);
  if (!moving) return columns;

  return columns.map((column) => {
    const cards = sortedCards(column).filter((card) => card.id !== moving.id);
    if (column.id === target.targetColumnId) {
      cards.splice(target.targetIndex, 0, {
        ...moving,
        columnId: target.targetColumnId,
      });
    }
    return {
      ...column,
      cards: cards.map((card, index) => ({ ...card, orderIndex: index })),
    };
  });
}

// Only Admins and Members drag; Guests and anyone else cannot.
export function canDragCards(role: string | undefined): boolean {
  return role === "admin" || role === "member";
}

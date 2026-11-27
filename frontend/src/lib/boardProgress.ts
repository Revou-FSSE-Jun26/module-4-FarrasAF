import type { BoardColumn } from "@/types/api";

// Analytics treats Columns named exactly "Done" as completed work (R9.3);
// the Board progress bar uses the same rule.
export const DONE_COLUMN_NAME = "Done";

export interface BoardProgressValue {
  done: number;
  total: number;
  // Whole number from 0 to 100, rounded to the nearest (6 of 10 is 60).
  percent: number;
}

// Cards in "Done" Columns divided by all Cards of the Board. A Board with no
// Cards has 0 of 0 and 0 percent.
export function boardProgress(
  columns: readonly BoardColumn[],
): BoardProgressValue {
  const total = columns.reduce((sum, column) => sum + column.cards.length, 0);
  const done = columns
    .filter((column) => column.name === DONE_COLUMN_NAME)
    .reduce((sum, column) => sum + column.cards.length, 0);
  return {
    done,
    total,
    percent: total === 0 ? 0 : Math.round((done / total) * 100),
  };
}

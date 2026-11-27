export const CHECKLIST_TEXT_MAX = 255;
export const CHECKLIST_MAX_ITEMS = 50;

export interface ChecklistProgressValue {
  done: number;
  total: number;
  // Whole number from 0 to 100, rounded to the nearest (1 of 3 is 33).
  percent: number;
}

// Progress of a to-do list, or null when the list is empty.
export function checklistProgress(
  items: readonly { isDone: boolean }[],
): ChecklistProgressValue | null {
  const total = items.length;
  if (total === 0) return null;
  const done = items.filter((item) => item.isDone).length;
  return { done, total, percent: Math.round((done / total) * 100) };
}

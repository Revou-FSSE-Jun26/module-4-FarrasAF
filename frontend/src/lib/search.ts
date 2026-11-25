export const SEARCH_MAX_LENGTH = 100;

// UX-only check; the server validates the keyword as well.
export function validateSearchKeyword(raw: string): string | null {
  const trimmed = raw.trim();
  if (trimmed.length < 1) return "Enter a keyword to search.";
  if (trimmed.length > SEARCH_MAX_LENGTH) {
    return `Keyword must be at most ${SEARCH_MAX_LENGTH} characters.`;
  }
  return null;
}

import { ApiError } from "@/lib/apiClient";

/** Shown whenever an error must not expose its details to the user. */
export const GENERIC_ERROR_MESSAGE = "Something went wrong. Please try again.";

/**
 * Maps any thrown value to a message that is safe to show in the UI.
 *
 * Only client errors (4xx) carry the backend's message, which is written to be
 * clear and actionable. Server errors (5xx), network failures, and unexpected
 * exceptions return the fixed `fallback`; their text is never shown.
 */
export function getErrorMessage(
  err: unknown,
  fallback: string = GENERIC_ERROR_MESSAGE,
): string {
  if (
    err instanceof ApiError &&
    err.status >= 400 &&
    err.status < 500 &&
    err.code !== "unknown_error"
  ) {
    return err.message;
  }
  return fallback;
}

/**
 * Writes error details to the browser console in development only.
 * Production builds log nothing, so no stack traces or messages leak.
 */
export function logError(err: unknown, context?: string): void {
  if (process.env.NODE_ENV === "production") return;
  console.error(context ? `[${context}]` : "[error]", err);
}

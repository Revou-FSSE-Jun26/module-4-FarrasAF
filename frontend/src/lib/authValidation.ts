// Client-side validation is for UX only; the server is authoritative.

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validateEmail(email: string): string | undefined {
  return EMAIL_PATTERN.test(email.trim())
    ? undefined
    : 'Enter a valid email address.';
}

export function validatePassword(password: string): string | undefined {
  return password.length >= 8
    ? undefined
    : 'Password must be at least 8 characters.';
}

export function validateDisplayName(displayName: string): string | undefined {
  const length = displayName.trim().length;
  return length >= 1 && length <= 50
    ? undefined
    : 'Display name must be 1 to 50 characters.';
}

export function validatePasswordConfirmation(
  password: string,
  confirmation: string,
): string | undefined {
  return password === confirmation ? undefined : 'Passwords do not match.';
}

/** Accept only same-site relative paths to avoid open redirects. */
export function safeNextPath(next: string | null): string {
  if (next && next.startsWith('/') && !next.startsWith('//')) {
    return next;
  }
  return '/boards';
}

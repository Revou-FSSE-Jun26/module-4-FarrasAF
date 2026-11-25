'use client';

import { useState } from 'react';
import type { FormEvent } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import BaseButton from '@/components/shared/BaseButton';
import BaseInput from '@/components/shared/BaseInput';
import useAuth from '@/hooks/useAuth';
import useToast from '@/hooks/useToast';
import { ApiError } from '@/lib/apiClient';
import { safeNextPath, validateEmail } from '@/lib/authValidation';

const GENERIC_LOGIN_ERROR = 'Invalid email or password.';

export default function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();
  const { showError } = useToast();
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [emailError, setEmailError] = useState<string | undefined>();
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    const invalidEmail = validateEmail(email);
    setEmailError(invalidEmail);
    if (invalidEmail || password.length === 0) {
      if (!invalidEmail) setFormError(GENERIC_LOGIN_ERROR);
      return;
    }
    setIsSubmitting(true);
    try {
      await login({ email: email.trim(), password });
      router.replace(safeNextPath(searchParams.get('next')));
    } catch (err: unknown) {
      if (err instanceof ApiError && err.status < 500) {
        // Never reveal whether the email, password, or lockout caused the failure.
        setFormError(GENERIC_LOGIN_ERROR);
      } else {
        // Server or network failure: the credentials were not the problem.
        showError(err);
      }
      setIsSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      className="flex w-full max-w-sm flex-col gap-4 rounded-lg border border-gray-200 bg-white p-6"
    >
      <h1 className="text-xl font-semibold text-gray-900">Log in</h1>
      <BaseInput
        label="Email"
        type="email"
        autoComplete="email"
        value={email}
        error={emailError}
        onChange={(e) => setEmail(e.target.value)}
      />
      <BaseInput
        label="Password"
        type="password"
        autoComplete="current-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      {formError ? (
        <p role="alert" className="text-sm text-red-600">
          {formError}
        </p>
      ) : null}
      <BaseButton type="submit" isLoading={isSubmitting}>
        Log in
      </BaseButton>
      <p className="text-sm text-gray-600">
        No account?{' '}
        <Link href="/register" className="text-blue-600 hover:underline">
          Register
        </Link>
      </p>
    </form>
  );
}

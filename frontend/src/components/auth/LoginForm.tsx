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
      // Reset so the form is usable again if this page is kept alive by the
      // router and shown again after logout.
      setIsSubmitting(false);
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
      className="rt-panel flex w-full max-w-md flex-col gap-5 p-7 lg:p-9"
    >
      <div>
        <p className="rt-kicker mb-4">Welcome back</p>
        <h1 className="text-3xl font-bold text-gray-900">Enter your workspace</h1>
        <p className="mt-2 text-sm text-gray-600">Pick up where your team left off.</p>
      </div>
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
      <p className="border-t border-[#211621]/15 pt-4 text-sm text-gray-600">
        No account?{' '}
        <Link href="/register" className="font-semibold text-[#3f2548] underline decoration-[#ff7965] decoration-2 underline-offset-4">
          Create one
        </Link>
      </p>
    </form>
  );
}

'use client';

import { useState } from 'react';
import type { FormEvent } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import BaseButton from '@/components/shared/BaseButton';
import BaseInput from '@/components/shared/BaseInput';
import useAuth from '@/hooks/useAuth';
import useToast from '@/hooks/useToast';
import { ApiError } from '@/lib/apiClient';
import {
  validateDisplayName,
  validateEmail,
  validatePassword,
} from '@/lib/authValidation';

interface FieldErrors {
  email?: string;
  password?: string;
  displayName?: string;
}

export default function RegisterForm() {
  const router = useRouter();
  const { register, login } = useAuth();
  const { showError } = useToast();
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [displayName, setDisplayName] = useState<string>('');
  const [errors, setErrors] = useState<FieldErrors>({});
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const clientErrors: FieldErrors = {
      email: validateEmail(email),
      password: validatePassword(password),
      displayName: validateDisplayName(displayName),
    };
    setErrors(clientErrors);
    if (Object.values(clientErrors).some(Boolean)) return;

    setIsSubmitting(true);
    try {
      await register({
        email: email.trim(),
        password,
        displayName: displayName.trim(),
      });
      await login({ email: email.trim(), password });
      router.replace('/boards');
    } catch (err: unknown) {
      const field = err instanceof ApiError ? err.field : undefined;
      if (err instanceof ApiError && err.status < 500 && field === 'email') {
        setErrors({ email: err.message });
      } else if (
        err instanceof ApiError &&
        err.status < 500 &&
        field === 'password'
      ) {
        setErrors({ password: err.message });
      } else if (
        err instanceof ApiError &&
        err.status < 500 &&
        field === 'displayName'
      ) {
        setErrors({ displayName: err.message });
      } else {
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
        <p className="rt-kicker mb-4">Start moving</p>
        <h1 className="text-3xl font-bold text-gray-900">Create your account</h1>
        <p className="mt-2 text-sm text-gray-600">A calmer way to make progress together.</p>
      </div>
      <BaseInput
        label="Display name"
        autoComplete="nickname"
        value={displayName}
        error={errors.displayName}
        onChange={(e) => setDisplayName(e.target.value)}
      />
      <BaseInput
        label="Email"
        type="email"
        autoComplete="email"
        value={email}
        error={errors.email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <BaseInput
        label="Password"
        type="password"
        autoComplete="new-password"
        value={password}
        error={errors.password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <BaseButton type="submit" isLoading={isSubmitting}>
        Register
      </BaseButton>
      <p className="border-t border-[#211621]/15 pt-4 text-sm text-gray-600">
        Already registered?{' '}
        <Link href="/login" className="font-semibold text-[#3f2548] underline decoration-[#ff7965] decoration-2 underline-offset-4">
          Log in
        </Link>
      </p>
    </form>
  );
}

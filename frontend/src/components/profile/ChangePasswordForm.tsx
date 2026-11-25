"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import BaseButton from "@/components/shared/BaseButton";
import BaseInput from "@/components/shared/BaseInput";
import type {
  PasswordFieldErrors,
  PasswordFormValues,
} from "@/hooks/useProfile";

interface ChangePasswordFormProps {
  errors: PasswordFieldErrors;
  isSaving: boolean;
  onPasswordChange: (values: PasswordFormValues) => Promise<boolean>;
}

export default function ChangePasswordForm({
  errors,
  isSaving,
  onPasswordChange,
}: ChangePasswordFormProps) {
  const [currentPassword, setCurrentPassword] = useState<string>("");
  const [newPassword, setNewPassword] = useState<string>("");
  const [confirmPassword, setConfirmPassword] = useState<string>("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const isChanged = await onPasswordChange({
      currentPassword,
      newPassword,
      confirmPassword,
    });
    if (isChanged) {
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      className="flex flex-col gap-4 rounded-lg border border-gray-200 bg-white p-6"
    >
      <h2 className="text-lg font-semibold text-gray-900">Change password</h2>
      <BaseInput
        label="Current password"
        type="password"
        autoComplete="current-password"
        value={currentPassword}
        error={errors.currentPassword}
        onChange={(e) => setCurrentPassword(e.target.value)}
      />
      <BaseInput
        label="New password"
        type="password"
        autoComplete="new-password"
        value={newPassword}
        error={errors.newPassword}
        onChange={(e) => setNewPassword(e.target.value)}
      />
      <BaseInput
        label="Confirm new password"
        type="password"
        autoComplete="new-password"
        value={confirmPassword}
        error={errors.confirmPassword}
        onChange={(e) => setConfirmPassword(e.target.value)}
      />
      <BaseButton type="submit" isLoading={isSaving} className="self-start">
        Change password
      </BaseButton>
    </form>
  );
}

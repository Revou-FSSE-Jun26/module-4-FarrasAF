"use client";

import { useCallback, useState } from "react";
import useAuth, { publishUser } from "@/hooks/useAuth";
import useToast from "@/hooks/useToast";
import { ApiError, apiClient } from "@/lib/apiClient";
import {
  validateDisplayName,
  validatePassword,
  validatePasswordConfirmation,
} from "@/lib/authValidation";
import type { User } from "@/types/api";

export interface PasswordFormValues {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

export interface PasswordFieldErrors {
  currentPassword?: string;
  newPassword?: string;
  confirmPassword?: string;
}

interface UseProfileResult {
  user: User | null;
  isLoading: boolean;
  loadError: string | null;
  displayNameError: string | undefined;
  passwordErrors: PasswordFieldErrors;
  isSavingName: boolean;
  isChangingPassword: boolean;
  /** Resolves true on success. */
  saveDisplayName: (displayName: string) => Promise<boolean>;
  /** Resolves true on success; the caller then clears its fields. */
  changePassword: (values: PasswordFormValues) => Promise<boolean>;
}

export default function useProfile(): UseProfileResult {
  const { user, isLoading, error } = useAuth({ shouldLoadUser: true });
  const { showError, showToast } = useToast();
  const [displayNameError, setDisplayNameError] = useState<string | undefined>();
  const [passwordErrors, setPasswordErrors] = useState<PasswordFieldErrors>({});
  const [isSavingName, setIsSavingName] = useState<boolean>(false);
  const [isChangingPassword, setIsChangingPassword] = useState<boolean>(false);

  const saveDisplayName = useCallback(
    async (displayName: string): Promise<boolean> => {
      const invalid = validateDisplayName(displayName);
      setDisplayNameError(invalid);
      if (invalid) return false;
      setIsSavingName(true);
      try {
        const updated = await apiClient.updateProfile({
          displayName: displayName.trim(),
        });
        publishUser(updated);
        showToast("Display name updated.", "success");
        return true;
      } catch (err: unknown) {
        showError(err, "Could not update your display name.");
        return false;
      } finally {
        setIsSavingName(false);
      }
    },
    [showError, showToast],
  );

  const changePassword = useCallback(
    async (values: PasswordFormValues): Promise<boolean> => {
      const errors: PasswordFieldErrors = {
        currentPassword:
          values.currentPassword.length === 0
            ? "Enter your current password."
            : undefined,
        newPassword: validatePassword(values.newPassword),
        confirmPassword: validatePasswordConfirmation(
          values.newPassword,
          values.confirmPassword,
        ),
      };
      setPasswordErrors(errors);
      if (errors.currentPassword || errors.newPassword || errors.confirmPassword) {
        return false;
      }
      setIsChangingPassword(true);
      try {
        // The server sets fresh cookies, so the User stays logged in.
        await apiClient.changePassword({
          currentPassword: values.currentPassword,
          newPassword: values.newPassword,
        });
        showToast("Password changed.", "success");
        return true;
      } catch (err: unknown) {
        if (
          err instanceof ApiError &&
          (err.field === "currentPassword" || err.field === "current_password")
        ) {
          setPasswordErrors({ currentPassword: err.message });
        } else {
          showError(err, "Could not change your password.");
        }
        return false;
      } finally {
        setIsChangingPassword(false);
      }
    },
    [showError, showToast],
  );

  return {
    user,
    isLoading,
    loadError: error,
    displayNameError,
    passwordErrors,
    isSavingName,
    isChangingPassword,
    saveDisplayName,
    changePassword,
  };
}

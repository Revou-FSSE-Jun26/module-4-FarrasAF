"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import useToast from "@/hooks/useToast";
import { ApiError, apiClient } from "@/lib/apiClient";
import type { LoginRequest, RegisterRequest, User } from "@/types/api";

// Lets every mounted useAuth (app shell, profile page) show the same user.
const userListeners = new Set<(user: User) => void>();

export function publishUser(user: User): void {
  userListeners.forEach((listener) => listener(user));
}

interface UseAuthOptions {
  /** Load the current user on mount (authenticated pages only). */
  shouldLoadUser?: boolean;
}

interface UseAuthResult {
  user: User | null;
  isLoading: boolean;
  error: string | null;
  login: (body: LoginRequest) => Promise<User>;
  register: (body: RegisterRequest) => Promise<User>;
  logout: () => Promise<void>;
}

export default function useAuth({
  shouldLoadUser = false,
}: UseAuthOptions = {}): UseAuthResult {
  const router = useRouter();
  const { showError } = useToast();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(shouldLoadUser);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!shouldLoadUser) return;
    let isActive = true;
    apiClient
      .getMe()
      .then((me) => {
        if (isActive) setUser(me);
      })
      .catch((err: unknown) => {
        // A 401 is handled by apiClient (redirect to /login).
        if (isActive && !(err instanceof ApiError && err.status === 401)) {
          const message = "Could not load your account. Please try again.";
          setError(message);
          showError(err, message);
        }
      })
      .finally(() => {
        if (isActive) setIsLoading(false);
      });
    return () => {
      isActive = false;
    };
  }, [shouldLoadUser, showError]);

  useEffect(() => {
    if (!shouldLoadUser) return;
    userListeners.add(setUser);
    return () => {
      userListeners.delete(setUser);
    };
  }, [shouldLoadUser]);

  const login = useCallback(async (body: LoginRequest): Promise<User> => {
    const me = await apiClient.login(body);
    setUser(me);
    return me;
  }, []);

  const register = useCallback(async (body: RegisterRequest): Promise<User> => {
    return apiClient.register(body);
  }, []);

  const logout = useCallback(async (): Promise<void> => {
    try {
      await apiClient.logout();
    } catch {
      // Leave the session screen regardless; the server revokes what it can.
    }
    setUser(null);
    router.replace("/login");
  }, [router]);

  return { user, isLoading, error, login, register, logout };
}

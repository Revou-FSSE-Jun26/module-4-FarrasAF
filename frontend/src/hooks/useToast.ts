"use client";

import { createContext, useContext } from "react";
import type { BaseToastVariant } from "@/components/shared/BaseToast";

export interface ToastContextValue {
  /** Show a message. Identical messages already on screen are not repeated. */
  showToast: (message: string, variant?: BaseToastVariant) => void;
  /**
   * Show an error toast for any thrown value. 4xx API errors show the backend
   * message; everything else shows `fallback`. Details go to the dev console.
   */
  showError: (err: unknown, fallback?: string) => void;
}

export const ToastContext = createContext<ToastContextValue | null>(null);

export default function useToast(): ToastContextValue {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used inside BaseToastProvider.");
  }
  return context;
}

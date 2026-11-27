"use client";

import { useCallback, useState } from "react";
import useToast from "@/hooks/useToast";
import { apiClient } from "@/lib/apiClient";

interface UseChecklistParams {
  cardId: string;
  // Refetches the Board so the Card (and its items) shows the saved state.
  onChecklistChange: () => Promise<void>;
}

interface UseChecklistResult {
  isBusy: boolean;
  addItem: (text: string) => Promise<boolean>;
  setItemDone: (itemId: string, isDone: boolean) => Promise<boolean>;
  renameItem: (itemId: string, text: string) => Promise<boolean>;
  removeItem: (itemId: string) => Promise<boolean>;
}

export default function useChecklist({
  cardId,
  onChecklistChange,
}: UseChecklistParams): UseChecklistResult {
  const { showError } = useToast();
  const [isBusy, setIsBusy] = useState<boolean>(false);

  const run = useCallback(
    async (action: () => Promise<unknown>, fallback: string) => {
      setIsBusy(true);
      try {
        await action();
        await onChecklistChange();
        return true;
      } catch (err: unknown) {
        showError(err, fallback);
        return false;
      } finally {
        setIsBusy(false);
      }
    },
    [onChecklistChange, showError],
  );

  const addItem = useCallback(
    (text: string) =>
      run(
        () => apiClient.createChecklistItem(cardId, { text }),
        "Could not add the to-do item.",
      ),
    [cardId, run],
  );

  const setItemDone = useCallback(
    (itemId: string, isDone: boolean) =>
      run(
        () => apiClient.updateChecklistItem(itemId, { isDone }),
        "Could not update the to-do item.",
      ),
    [run],
  );

  const renameItem = useCallback(
    (itemId: string, text: string) =>
      run(
        () => apiClient.updateChecklistItem(itemId, { text }),
        "Could not update the to-do item.",
      ),
    [run],
  );

  const removeItem = useCallback(
    (itemId: string) =>
      run(
        () => apiClient.deleteChecklistItem(itemId),
        "Could not delete the to-do item.",
      ),
    [run],
  );

  return { isBusy, addItem, setItemDone, renameItem, removeItem };
}

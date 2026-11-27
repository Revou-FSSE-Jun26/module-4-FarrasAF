"use client";

import { useCallback, useState } from "react";
import useToast from "@/hooks/useToast";
import { apiClient } from "@/lib/apiClient";
import { validateAttachmentFile } from "@/lib/attachments";

interface UseAttachmentsParams {
  cardId: string;
  // Refetches the Board so the Card shows the saved attachments.
  onAttachmentsChange: () => Promise<void>;
}

interface UseAttachmentsResult {
  isBusy: boolean;
  // Message for the file the user picked, shown next to the picker.
  fileError: string | undefined;
  upload: (file: File) => Promise<boolean>;
  remove: (attachmentId: string) => Promise<boolean>;
}

export default function useAttachments({
  cardId,
  onAttachmentsChange,
}: UseAttachmentsParams): UseAttachmentsResult {
  const { showError } = useToast();
  const [isBusy, setIsBusy] = useState<boolean>(false);
  const [fileError, setFileError] = useState<string | undefined>();

  const run = useCallback(
    async (action: () => Promise<unknown>, fallback: string) => {
      setIsBusy(true);
      try {
        await action();
        await onAttachmentsChange();
        return true;
      } catch (err: unknown) {
        showError(err, fallback);
        return false;
      } finally {
        setIsBusy(false);
      }
    },
    [onAttachmentsChange, showError],
  );

  const upload = useCallback(
    async (file: File) => {
      const message = validateAttachmentFile(file);
      setFileError(message);
      if (message) return false;
      return run(
        () => apiClient.uploadAttachment(cardId, file),
        "Could not upload the file.",
      );
    },
    [cardId, run],
  );

  const remove = useCallback(
    (attachmentId: string) =>
      run(
        () => apiClient.deleteAttachment(attachmentId),
        "Could not delete the attachment.",
      ),
    [run],
  );

  return { isBusy, fileError, upload, remove };
}

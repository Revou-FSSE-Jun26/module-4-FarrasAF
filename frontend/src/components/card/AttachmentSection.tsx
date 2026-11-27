"use client";

import { useState } from "react";
import type { ChangeEvent } from "react";
import AttachmentRow from "@/components/card/AttachmentRow";
import BaseButton from "@/components/shared/BaseButton";
import useAttachments from "@/hooks/useAttachments";
import { ATTACHMENT_ACCEPT, ATTACHMENT_MAX_COUNT } from "@/lib/attachments";
import type { Attachment, BoardRole } from "@/types/api";

interface AttachmentSectionProps {
  cardId: string;
  attachments: Attachment[];
  currentUserId: string | null;
  currentUserRole: BoardRole;
  onAttachmentsChange: () => Promise<void>;
}

export default function AttachmentSection({
  cardId,
  attachments,
  currentUserId,
  currentUserRole,
  onAttachmentsChange,
}: AttachmentSectionProps) {
  const { isBusy, fileError, upload, remove } = useAttachments({
    cardId,
    onAttachmentsChange,
  });
  const [file, setFile] = useState<File | null>(null);
  // Changing the key clears the native file input after a successful upload.
  const [inputKey, setInputKey] = useState<number>(0);

  const isAdmin = currentUserRole === "admin";
  const canUpload = isAdmin || currentUserRole === "member";
  const isFull = attachments.length >= ATTACHMENT_MAX_COUNT;

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] ?? null);
  }

  async function handleUpload() {
    if (!file) return;
    if (await upload(file)) {
      setFile(null);
      setInputKey((key) => key + 1);
    }
  }

  return (
    <section aria-label="Attachments" className="flex flex-col gap-2.5">
      <div className="flex items-baseline justify-between gap-2">
        <h3 className="text-sm font-medium text-slate-700">Attachments</h3>
        <span className="text-xs text-slate-500 tabular-nums">
          {attachments.length}/{ATTACHMENT_MAX_COUNT}
        </span>
      </div>
      {attachments.length > 0 ? (
        <ul className="flex flex-col gap-1.5">
          {attachments.map((attachment) => (
            <AttachmentRow
              key={attachment.id}
              attachment={attachment}
              canDelete={isAdmin || attachment.uploadedBy.id === currentUserId}
              isDisabled={isBusy}
              onAttachmentDelete={() => void remove(attachment.id)}
            />
          ))}
        </ul>
      ) : (
        <p className="text-xs text-slate-400">No attachments yet</p>
      )}
      {canUpload ? (
        isFull ? (
          <p className="text-xs text-slate-500">
            A Card can have at most {ATTACHMENT_MAX_COUNT} attachments.
          </p>
        ) : (
          <div className="flex flex-col gap-1.5">
            <div className="flex flex-wrap items-center gap-2">
              <input
                key={inputKey}
                type="file"
                aria-label="Choose file"
                accept={ATTACHMENT_ACCEPT}
                disabled={isBusy}
                onChange={handleFileChange}
                className="min-w-0 flex-1 text-sm text-slate-700 file:mr-3 file:rounded-lg file:border file:border-slate-200 file:bg-white file:px-3 file:py-1.5 file:text-sm"
              />
              <BaseButton
                variant="secondary"
                isLoading={isBusy}
                disabled={!file}
                onClick={() => void handleUpload()}
              >
                Upload
              </BaseButton>
            </div>
            <p className="text-xs text-slate-500">
              Images, PDF, DOCX, XLSX, PPTX, TXT or CSV. Up to 5 MB each.
            </p>
            {fileError ? (
              <p role="alert" className="text-xs font-medium text-rose-600">
                {fileError}
              </p>
            ) : null}
          </div>
        )
      ) : null}
    </section>
  );
}

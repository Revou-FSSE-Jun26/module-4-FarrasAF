"use client";

import BaseButton from "@/components/shared/BaseButton";
import { formatFileSize } from "@/lib/attachments";
import type { Attachment } from "@/types/api";

interface AttachmentRowProps {
  attachment: Attachment;
  canDelete: boolean;
  isDisabled: boolean;
  onAttachmentDelete: () => void;
}

export default function AttachmentRow({
  attachment,
  canDelete,
  isDisabled,
  onAttachmentDelete,
}: AttachmentRowProps) {
  return (
    <li className="flex items-center justify-between gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2">
      <div className="flex min-w-0 flex-col">
        <a
          href={attachment.downloadUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="truncate text-sm font-medium text-indigo-700 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/40"
        >
          {attachment.fileName}
        </a>
        <span className="text-xs text-slate-500">
          {formatFileSize(attachment.sizeBytes)} ·{" "}
          {attachment.uploadedBy.displayName}
        </span>
      </div>
      {canDelete ? (
        <BaseButton
          variant="secondary"
          size="sm"
          disabled={isDisabled}
          aria-label={`Delete ${attachment.fileName}`}
          onClick={onAttachmentDelete}
        >
          Delete
        </BaseButton>
      ) : null}
    </li>
  );
}

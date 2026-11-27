"use client";

import type { FormEvent } from "react";
import BaseButton from "@/components/shared/BaseButton";
import BaseInput from "@/components/shared/BaseInput";
import AttachmentSection from "@/components/card/AttachmentSection";
import ChecklistProgress from "@/components/card/ChecklistProgress";
import ChecklistSection from "@/components/card/ChecklistSection";
import CommentSection from "@/components/comment/CommentSection";
import BaseModal from "@/components/shared/BaseModal";
import useCardDetail from "@/hooks/useCardDetail";
import type { BoardRole, Card } from "@/types/api";

interface CardDetailModalProps {
  boardId: string;
  card: Card;
  currentUserId: string | null;
  currentUserRole: BoardRole;
  onCardChange: () => Promise<void>;
  onClose: () => void;
}

const FIELD_CLASSES =
  "min-h-10 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-2xs transition-colors hover:border-slate-300 focus:outline-none focus-visible:border-indigo-500 focus-visible:ring-2 focus-visible:ring-indigo-500/25";

export default function CardDetailModal({
  boardId,
  card,
  currentUserId,
  currentUserRole,
  onCardChange,
  onClose,
}: CardDetailModalProps) {
  const detail = useCardDetail({ boardId, card, onCardChange, onClose });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void detail.save();
  }

  return (
    <BaseModal isOpen title="Card details" onClose={onClose}>
      <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
        {detail.notice ? (
          <p
            role="status"
            className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2.5 text-sm text-amber-900"
          >
            {detail.notice}
          </p>
        ) : null}

        <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
          <BaseInput
            label="Title"
            value={detail.title}
            error={detail.titleError}
            maxLength={255}
            onChange={(e) => detail.setTitle(e.target.value)}
          />
          {card.checklistItems.length > 0 ? (
            <div className="w-full sm:w-52 sm:shrink-0">
              <ChecklistProgress items={card.checklistItems} />
            </div>
          ) : null}
        </div>

        <div className="flex flex-col gap-1.5">
          <label
            htmlFor="card-description"
            className="text-sm font-medium text-slate-700"
          >
            Description
          </label>
          <textarea
            id="card-description"
            rows={4}
            placeholder="Add a more detailed description..."
            value={detail.description}
            maxLength={5000}
            aria-invalid={detail.descriptionError ? true : undefined}
            onChange={(e) => detail.setDescription(e.target.value)}
            className={FIELD_CLASSES}
          />
          {detail.descriptionError ? (
            <p role="alert" className="text-xs font-medium text-rose-600">
              {detail.descriptionError}
            </p>
          ) : null}
        </div>

        <div className="flex flex-col gap-1.5">
          <label
            htmlFor="card-assignee"
            className="text-sm font-medium text-slate-700"
          >
            Assignee
          </label>
          <select
            id="card-assignee"
            value={detail.assigneeId}
            onChange={(e) => detail.setAssigneeId(e.target.value)}
            className={FIELD_CLASSES}
          >
            <option value="">Unassigned</option>
            {detail.members.map((member) => (
              <option key={member.userId} value={member.userId}>
                {member.displayName}
              </option>
            ))}
          </select>
        </div>

        <BaseInput
          label="Due date"
          type="date"
          value={detail.dueDate}
          onChange={(e) => detail.setDueDate(e.target.value)}
        />

        <ChecklistSection
          cardId={card.id}
          items={card.checklistItems}
          onChecklistChange={onCardChange}
        />

        <AttachmentSection
          cardId={card.id}
          attachments={card.attachments}
          currentUserId={currentUserId}
          currentUserRole={currentUserRole}
          onAttachmentsChange={onCardChange}
        />

        {detail.isConfirmingDelete ? (
          <div className="flex flex-col gap-2.5 rounded-lg border border-rose-200 bg-rose-50/70 p-3">
            <p className="text-sm font-medium text-rose-900">
              Delete this Card? This cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <BaseButton
                variant="secondary"
                size="sm"
                onClick={() => detail.setIsConfirmingDelete(false)}
              >
                Cancel
              </BaseButton>
              <BaseButton
                variant="danger"
                size="sm"
                isLoading={detail.isDeleting}
                onClick={() => void detail.remove()}
              >
                Confirm delete
              </BaseButton>
            </div>
          </div>
        ) : (
          <div className="flex flex-wrap justify-between gap-2 border-t border-slate-100 pt-3">
            <BaseButton
              variant="danger"
              onClick={() => detail.setIsConfirmingDelete(true)}
            >
              Delete card
            </BaseButton>
            <div className="flex gap-2">
              <BaseButton variant="secondary" onClick={onClose}>
                Cancel
              </BaseButton>
              <BaseButton type="submit" isLoading={detail.isSaving}>
                Save
              </BaseButton>
            </div>
          </div>
        )}
      </form>
      <div className="mt-5 border-t border-slate-100 pt-4">
        <CommentSection cardId={card.id} members={detail.members} />
      </div>
    </BaseModal>
  );
}

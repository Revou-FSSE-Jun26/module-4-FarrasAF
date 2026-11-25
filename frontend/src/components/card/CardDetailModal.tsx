"use client";

import type { FormEvent } from "react";
import BaseButton from "@/components/shared/BaseButton";
import BaseInput from "@/components/shared/BaseInput";
import CommentSection from "@/components/comment/CommentSection";
import BaseModal from "@/components/shared/BaseModal";
import useCardDetail from "@/hooks/useCardDetail";
import type { Card } from "@/types/api";

interface CardDetailModalProps {
  boardId: string;
  card: Card;
  onCardChange: () => Promise<void>;
  onClose: () => void;
}

const FIELD_CLASSES =
  "min-h-10 w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500";

export default function CardDetailModal({
  boardId,
  card,
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
      <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-3">
        {detail.notice ? (
          <p
            role="status"
            className="rounded-md bg-yellow-100 p-2 text-sm text-yellow-900"
          >
            {detail.notice}
          </p>
        ) : null}

        <BaseInput
          label="Title"
          value={detail.title}
          error={detail.titleError}
          maxLength={255}
          onChange={(e) => detail.setTitle(e.target.value)}
        />

        <div className="flex flex-col gap-1">
          <label
            htmlFor="card-description"
            className="text-sm font-medium text-gray-900"
          >
            Description
          </label>
          <textarea
            id="card-description"
            rows={5}
            value={detail.description}
            maxLength={5000}
            aria-invalid={detail.descriptionError ? true : undefined}
            onChange={(e) => detail.setDescription(e.target.value)}
            className={FIELD_CLASSES}
          />
          {detail.descriptionError ? (
            <p role="alert" className="text-sm text-red-600">
              {detail.descriptionError}
            </p>
          ) : null}
        </div>

        <div className="flex flex-col gap-1">
          <label
            htmlFor="card-assignee"
            className="text-sm font-medium text-gray-900"
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

        {detail.isConfirmingDelete ? (
          <div className="flex flex-col gap-2 rounded-md border border-red-200 p-3">
            <p className="text-sm text-gray-700">
              Delete this Card? This cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <BaseButton
                variant="secondary"
                onClick={() => detail.setIsConfirmingDelete(false)}
              >
                Cancel
              </BaseButton>
              <BaseButton
                variant="danger"
                isLoading={detail.isDeleting}
                onClick={() => void detail.remove()}
              >
                Confirm delete
              </BaseButton>
            </div>
          </div>
        ) : (
          <div className="flex flex-wrap justify-between gap-2">
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
      <CommentSection cardId={card.id} members={detail.members} />
    </BaseModal>
  );
}

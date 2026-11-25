"use client";

import { useCallback, useEffect, useState } from "react";
import useToast from "@/hooks/useToast";
import { ApiError, apiClient } from "@/lib/apiClient";
import type { BoardMember, Card, UpdateCardRequest } from "@/types/api";

const TITLE_MAX = 255;
const DESCRIPTION_MAX = 5000;

interface UseCardDetailParams {
  boardId: string;
  card: Card;
  onCardChange: () => Promise<void>;
  onClose: () => void;
}

interface UseCardDetailResult {
  title: string;
  description: string;
  assigneeId: string;
  dueDate: string;
  members: BoardMember[];
  titleError: string | undefined;
  descriptionError: string | undefined;
  notice: string | null;
  isSaving: boolean;
  isDeleting: boolean;
  isConfirmingDelete: boolean;
  setTitle: (value: string) => void;
  setDescription: (value: string) => void;
  setAssigneeId: (value: string) => void;
  setDueDate: (value: string) => void;
  setIsConfirmingDelete: (value: boolean) => void;
  save: () => Promise<void>;
  remove: () => Promise<void>;
}

export default function useCardDetail({
  boardId,
  card,
  onCardChange,
  onClose,
}: UseCardDetailParams): UseCardDetailResult {
  const { showError } = useToast();
  const [title, setTitle] = useState<string>(card.title);
  const [description, setDescription] = useState<string>(card.description);
  const [assigneeId, setAssigneeId] = useState<string>(card.assigneeId ?? "");
  const [dueDate, setDueDate] = useState<string>(card.dueDate ?? "");
  // The base Card the form was loaded from; its version is sent on every edit.
  const [base, setBase] = useState<Card>(card);
  const [members, setMembers] = useState<BoardMember[]>([]);
  const [titleError, setTitleError] = useState<string | undefined>();
  const [descriptionError, setDescriptionError] = useState<
    string | undefined
  >();
  const [notice, setNotice] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);
  const [isConfirmingDelete, setIsConfirmingDelete] = useState<boolean>(false);

  useEffect(() => {
    let isActive = true;
    apiClient
      .listBoardMembers(boardId)
      .then((res) => {
        if (isActive) setMembers(res.items);
      })
      .catch((err: unknown) => {
        if (isActive) showError(err, "Could not load Board members.");
      });
    return () => {
      isActive = false;
    };
  }, [boardId, showError]);

  const loadForm = useCallback((source: Card) => {
    setBase(source);
    setTitle(source.title);
    setDescription(source.description);
    setAssigneeId(source.assigneeId ?? "");
    setDueDate(source.dueDate ?? "");
  }, []);

  const save = useCallback(async () => {
    const trimmedTitle = title.trim();
    const trimmedDescription = description.trim();
    let isValid = true;
    setTitleError(undefined);
    setDescriptionError(undefined);
    if (trimmedTitle.length < 1 || trimmedTitle.length > TITLE_MAX) {
      setTitleError(`Title must be 1 to ${TITLE_MAX} characters.`);
      isValid = false;
    }
    if (trimmedDescription.length > DESCRIPTION_MAX) {
      setDescriptionError(
        `Description must be at most ${DESCRIPTION_MAX} characters.`,
      );
      isValid = false;
    }
    if (!isValid) return;

    const body: UpdateCardRequest = { version: base.version };
    if (trimmedTitle !== base.title) body.title = trimmedTitle;
    if (trimmedDescription !== base.description) {
      body.description = trimmedDescription;
    }
    if (assigneeId !== (base.assigneeId ?? "")) {
      body.assigneeId = assigneeId === "" ? null : assigneeId;
    }
    if (dueDate !== (base.dueDate ?? "")) {
      body.dueDate = dueDate === "" ? null : dueDate;
    }
    if (Object.keys(body).length === 1) {
      onClose();
      return;
    }

    setNotice(null);
    setIsSaving(true);
    try {
      await apiClient.updateCard(base.id, body);
      await onCardChange();
      onClose();
    } catch (err: unknown) {
      if (err instanceof ApiError && err.isConflict) {
        try {
          loadForm(await apiClient.getCard(base.id));
          await onCardChange();
          setNotice(
            "Someone else changed this Card. The latest version was loaded; review it and save again.",
          );
        } catch (reloadErr: unknown) {
          showError(reloadErr, "This Card changed and could not be reloaded.");
        }
      } else {
        showError(err, "Could not save the Card.");
      }
    } finally {
      setIsSaving(false);
    }
  }, [
    title,
    description,
    assigneeId,
    dueDate,
    base,
    onCardChange,
    onClose,
    loadForm,
    showError,
  ]);

  const remove = useCallback(async () => {
    setIsDeleting(true);
    try {
      await apiClient.deleteCard(base.id);
      await onCardChange();
      onClose();
    } catch (err: unknown) {
      showError(err, "Could not delete the Card.");
      setIsConfirmingDelete(false);
    } finally {
      setIsDeleting(false);
    }
  }, [base.id, onCardChange, onClose, showError]);

  return {
    title,
    description,
    assigneeId,
    dueDate,
    members,
    titleError,
    descriptionError,
    notice,
    isSaving,
    isDeleting,
    isConfirmingDelete,
    setTitle,
    setDescription,
    setAssigneeId,
    setDueDate,
    setIsConfirmingDelete,
    save,
    remove,
  };
}

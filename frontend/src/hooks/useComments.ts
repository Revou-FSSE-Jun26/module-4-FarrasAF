"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import useToast from "@/hooks/useToast";
import { ApiError, apiClient } from "@/lib/apiClient";
import { buildCommentTree } from "@/lib/comments";
import type { CommentNode } from "@/lib/comments";
import type { Comment } from "@/types/api";

const BODY_MAX = 5000;

interface UseCommentsResult {
  tree: CommentNode[];
  currentUserId: string | null;
  isLoading: boolean;
  loadError: string | null;
  error: string | null;
  notice: string | null;
  isBusy: boolean;
  add: (body: string, parentCommentId: string | null) => Promise<boolean>;
  edit: (comment: Comment, body: string) => Promise<boolean>;
  remove: (commentId: string) => Promise<void>;
}

function validateBody(body: string): string | null {
  const trimmed = body.trim();
  if (trimmed.length < 1) return "Comment cannot be empty.";
  if (trimmed.length > BODY_MAX) {
    return `Comment must be at most ${BODY_MAX} characters.`;
  }
  return null;
}

export default function useComments(cardId: string): UseCommentsResult {
  const { showError } = useToast();
  const [comments, setComments] = useState<Comment[]>([]);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [isBusy, setIsBusy] = useState<boolean>(false);

  const reload = useCallback(async () => {
    const res = await apiClient.listComments(cardId);
    setComments(res.items);
  }, [cardId]);

  useEffect(() => {
    let isActive = true;
    Promise.all([apiClient.listComments(cardId), apiClient.getMe()])
      .then(([list, me]) => {
        if (!isActive) return;
        setComments(list.items);
        setCurrentUserId(me.id);
      })
      .catch((err: unknown) => {
        if (!isActive) return;
        setLoadError("Could not load comments.");
        showError(err, "Could not load comments.");
      })
      .finally(() => {
        if (isActive) setIsLoading(false);
      });
    return () => {
      isActive = false;
    };
  }, [cardId, showError]);

  const run = useCallback(
    async (action: () => Promise<void>, fallback: string): Promise<boolean> => {
      setError(null);
      setNotice(null);
      setIsBusy(true);
      try {
        await action();
        return true;
      } catch (err: unknown) {
        if (err instanceof ApiError && err.isConflict) {
          setNotice(
            "Someone else changed this comment. The latest comments were loaded; review and try again.",
          );
          try {
            await reload();
          } catch (reloadErr: unknown) {
            showError(reloadErr, "Comments changed and could not be reloaded.");
          }
        } else {
          showError(err, fallback);
        }
        return false;
      } finally {
        setIsBusy(false);
      }
    },
    [reload, showError],
  );

  const add = useCallback(
    async (body: string, parentCommentId: string | null) => {
      const problem = validateBody(body);
      if (problem) {
        setError(problem);
        return false;
      }
      return run(async () => {
        await apiClient.createComment(cardId, {
          body: body.trim(),
          parentCommentId,
        });
        await reload();
      }, "Could not post the comment.");
    },
    [cardId, reload, run],
  );

  const edit = useCallback(
    async (comment: Comment, body: string) => {
      const problem = validateBody(body);
      if (problem) {
        setError(problem);
        return false;
      }
      return run(async () => {
        await apiClient.updateComment(comment.id, {
          body: body.trim(),
          version: comment.version,
        });
        await reload();
      }, "Could not edit the comment.");
    },
    [reload, run],
  );

  const remove = useCallback(
    async (commentId: string) => {
      await run(async () => {
        await apiClient.deleteComment(commentId);
        await reload();
      }, "Could not delete the comment.");
    },
    [reload, run],
  );

  const tree = useMemo(() => buildCommentTree(comments), [comments]);

  return {
    tree,
    currentUserId,
    isLoading,
    loadError,
    error,
    notice,
    isBusy,
    add,
    edit,
    remove,
  };
}

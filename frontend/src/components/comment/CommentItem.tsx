"use client";

import { useState } from "react";
import CommentComposer from "@/components/comment/CommentComposer";
import BaseButton from "@/components/shared/BaseButton";
import { renderMentions } from "@/lib/comments";
import type { CommentNode } from "@/lib/comments";
import type { BoardMember, Comment } from "@/types/api";

interface CommentItemProps {
  node: CommentNode;
  members: BoardMember[];
  currentUserId: string | null;
  isBusy: boolean;
  onReplyEvent: (body: string, parentCommentId: string) => Promise<boolean>;
  onEditEvent: (comment: Comment, body: string) => Promise<boolean>;
  onDeleteEvent: (commentId: string) => Promise<void>;
}

type Mode = "view" | "reply" | "edit" | "confirmDelete";

export default function CommentItem({
  node,
  members,
  currentUserId,
  isBusy,
  onReplyEvent,
  onEditEvent,
  onDeleteEvent,
}: CommentItemProps) {
  const { comment, replies } = node;
  const [mode, setMode] = useState<Mode>("view");
  const isOwn = currentUserId !== null && comment.authorId === currentUserId;
  const author = members.find((m) => m.userId === comment.authorId);

  return (
    <li className="flex flex-col gap-2">
      <div className="rounded-lg border border-slate-200/80 bg-slate-50/70 p-3">
        <p className="text-xs text-slate-500">
          <span className="font-medium text-slate-700">
            {author ? author.displayName : "Unknown user"}
          </span>{" "}
          · {new Date(comment.createdAt).toLocaleString()}
          {comment.editedAt ? " (edited)" : ""}
        </p>
        {mode === "edit" ? (
          <div className="mt-2">
            <CommentComposer
              label="Edit comment"
              submitLabel="Save"
              initialBody={comment.body}
              members={members}
              isBusy={isBusy}
              onSubmitEvent={async (body) => {
                const isOk = await onEditEvent(comment, body);
                if (isOk) setMode("view");
                return isOk;
              }}
              onCancelEvent={() => setMode("view")}
            />
          </div>
        ) : (
          <p className="mt-1 text-sm break-words whitespace-pre-wrap text-slate-800">
            {renderMentions(comment.body, members)}
          </p>
        )}
        {mode === "view" ? (
          <div className="mt-2 flex gap-1.5">
            <BaseButton
              variant="ghost"
              size="sm"
              onClick={() => setMode("reply")}
            >
              Reply
            </BaseButton>
            {isOwn ? (
              <>
                <BaseButton
                  variant="ghost"
                  size="sm"
                  onClick={() => setMode("edit")}
                >
                  Edit
                </BaseButton>
                <BaseButton
                  variant="ghost"
                  size="sm"
                  className="text-rose-600 hover:bg-rose-50 hover:text-rose-700"
                  onClick={() => setMode("confirmDelete")}
                >
                  Delete
                </BaseButton>
              </>
            ) : null}
          </div>
        ) : null}
        {mode === "confirmDelete" ? (
          <div className="mt-2.5 flex flex-col gap-2 rounded-lg border border-rose-200 bg-rose-50/70 p-2.5">
            <p className="text-xs font-medium text-rose-900">
              Delete this comment and its replies?
            </p>
            <div className="flex gap-2">
              <BaseButton
                variant="secondary"
                size="sm"
                onClick={() => setMode("view")}
              >
                Cancel
              </BaseButton>
              <BaseButton
                variant="danger"
                size="sm"
                isLoading={isBusy}
                onClick={() => void onDeleteEvent(comment.id)}
              >
                Confirm delete
              </BaseButton>
            </div>
          </div>
        ) : null}
        {mode === "reply" ? (
          <div className="mt-2.5">
            <CommentComposer
              label="Reply"
              submitLabel="Post reply"
              members={members}
              isBusy={isBusy}
              onSubmitEvent={async (body) => {
                const isOk = await onReplyEvent(body, comment.id);
                if (isOk) setMode("view");
                return isOk;
              }}
              onCancelEvent={() => setMode("view")}
            />
          </div>
        ) : null}
      </div>
      {replies.length > 0 ? (
        <ul className="ml-4 flex flex-col gap-2 border-l-2 border-slate-200/80 pl-3">
          {replies.map((reply) => (
            <CommentItem
              key={reply.comment.id}
              node={reply}
              members={members}
              currentUserId={currentUserId}
              isBusy={isBusy}
              onReplyEvent={onReplyEvent}
              onEditEvent={onEditEvent}
              onDeleteEvent={onDeleteEvent}
            />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

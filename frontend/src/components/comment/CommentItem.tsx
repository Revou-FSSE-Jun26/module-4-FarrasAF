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
      <div className="rounded-md border border-gray-200 p-2">
        <p className="text-xs text-gray-600">
          {author ? author.displayName : "Unknown user"} ·{" "}
          {new Date(comment.createdAt).toLocaleString()}
          {comment.editedAt ? " (edited)" : ""}
        </p>
        {mode === "edit" ? (
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
        ) : (
          <p className="text-sm break-words whitespace-pre-wrap text-gray-900">
            {renderMentions(comment.body, members)}
          </p>
        )}
        {mode === "view" ? (
          <div className="mt-1 flex gap-2">
            <BaseButton variant="secondary" onClick={() => setMode("reply")}>
              Reply
            </BaseButton>
            {isOwn ? (
              <>
                <BaseButton variant="secondary" onClick={() => setMode("edit")}>
                  Edit
                </BaseButton>
                <BaseButton
                  variant="danger"
                  onClick={() => setMode("confirmDelete")}
                >
                  Delete
                </BaseButton>
              </>
            ) : null}
          </div>
        ) : null}
        {mode === "confirmDelete" ? (
          <div className="mt-2 flex flex-col gap-2">
            <p className="text-sm text-gray-700">
              Delete this comment and its replies?
            </p>
            <div className="flex gap-2">
              <BaseButton variant="secondary" onClick={() => setMode("view")}>
                Cancel
              </BaseButton>
              <BaseButton
                variant="danger"
                isLoading={isBusy}
                onClick={() => void onDeleteEvent(comment.id)}
              >
                Confirm delete
              </BaseButton>
            </div>
          </div>
        ) : null}
        {mode === "reply" ? (
          <div className="mt-2">
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
        <ul className="ml-4 flex flex-col gap-2 border-l border-gray-200 pl-2">
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

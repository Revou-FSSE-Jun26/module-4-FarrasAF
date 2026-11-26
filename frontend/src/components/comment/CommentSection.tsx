"use client";

import CommentComposer from "@/components/comment/CommentComposer";
import CommentItem from "@/components/comment/CommentItem";
import useComments from "@/hooks/useComments";
import type { BoardMember } from "@/types/api";

interface CommentSectionProps {
  cardId: string;
  members: BoardMember[];
}

export default function CommentSection({
  cardId,
  members,
}: CommentSectionProps) {
  const comments = useComments(cardId);

  return (
    <section aria-label="Comments" className="flex flex-col gap-3">
      <h3 className="text-sm font-semibold tracking-tight text-slate-900">
        Comments
      </h3>
      {comments.notice ? (
        <p
          role="status"
          className="rounded-lg border border-amber-200 bg-amber-50 p-2.5 text-sm text-amber-900"
        >
          {comments.notice}
        </p>
      ) : null}
      {comments.error ? (
        <p role="alert" className="text-xs font-medium text-rose-600">
          {comments.error}
        </p>
      ) : null}
      {comments.isLoading ? (
        <p className="text-sm text-slate-500">Loading comments…</p>
      ) : comments.loadError ? (
        <p role="alert" className="text-xs font-medium text-rose-600">
          {comments.loadError}
        </p>
      ) : (
        <>
          {comments.tree.length === 0 ? (
            <p className="text-sm text-slate-500">No comments yet.</p>
          ) : (
            <ul className="flex flex-col gap-2.5">
              {comments.tree.map((node) => (
                <CommentItem
                  key={node.comment.id}
                  node={node}
                  members={members}
                  currentUserId={comments.currentUserId}
                  isBusy={comments.isBusy}
                  onReplyEvent={comments.add}
                  onEditEvent={comments.edit}
                  onDeleteEvent={comments.remove}
                />
              ))}
            </ul>
          )}
          <CommentComposer
            label="Add a comment"
            submitLabel="Comment"
            members={members}
            isBusy={comments.isBusy}
            onSubmitEvent={(body) => comments.add(body, null)}
          />
        </>
      )}
    </section>
  );
}

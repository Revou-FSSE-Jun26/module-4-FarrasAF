import type { BoardMember, Comment } from "@/types/api";

export interface CommentLike {
  id: string;
  parentCommentId: string | null;
}

export interface CommentNode<T extends CommentLike = Comment> {
  comment: T;
  replies: CommentNode<T>[];
}

/** Builds the thread tree from the flat list (oldest first). Orphans become roots. */
export function buildCommentTree<T extends CommentLike>(
  comments: T[],
): CommentNode<T>[] {
  const nodes = new Map<string, CommentNode<T>>();
  for (const comment of comments) {
    nodes.set(comment.id, { comment, replies: [] });
  }
  const roots: CommentNode<T>[] = [];
  for (const comment of comments) {
    const node = nodes.get(comment.id);
    if (!node) continue;
    const parent =
      comment.parentCommentId !== null
        ? nodes.get(comment.parentCommentId)
        : undefined;
    if (parent) parent.replies.push(node);
    else roots.push(node);
  }
  return roots;
}

const MENTION_PATTERN = /@\[([^\]]+)\]/g;

/** Replaces `@[<userId>]` tokens with plain-text `@displayName` (or `@unknown`). */
export function renderMentions(body: string, members: BoardMember[]): string {
  return body.replace(MENTION_PATTERN, (_match, userId: string) => {
    const member = members.find((m) => m.userId === userId);
    return `@${member ? member.displayName : "unknown"}`;
  });
}

export function mentionToken(userId: string): string {
  return `@[${userId}]`;
}

"use client";

import { useId, useState } from "react";
import type { FormEvent } from "react";
import BaseButton from "@/components/shared/BaseButton";
import { mentionToken } from "@/lib/comments";
import type { BoardMember } from "@/types/api";

interface CommentComposerProps {
  label: string;
  submitLabel: string;
  initialBody?: string;
  members: BoardMember[];
  isBusy: boolean;
  onSubmitEvent: (body: string) => Promise<boolean>;
  onCancelEvent?: () => void;
}

export default function CommentComposer({
  label,
  submitLabel,
  initialBody = "",
  members,
  isBusy,
  onSubmitEvent,
  onCancelEvent,
}: CommentComposerProps) {
  const [body, setBody] = useState<string>(initialBody);
  const fieldId = useId();

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (await onSubmitEvent(body)) setBody("");
  }

  function handleMention(userId: string) {
    if (userId === "") return;
    setBody(
      (prev) =>
        `${prev}${prev && !prev.endsWith(" ") ? " " : ""}${mentionToken(userId)} `,
    );
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-2">
      <label htmlFor={fieldId} className="text-sm font-medium text-slate-700">
        {label}
      </label>
      <textarea
        id={fieldId}
        rows={3}
        placeholder="Write a comment..."
        value={body}
        maxLength={5000}
        onChange={(e) => setBody(e.target.value)}
        className="min-h-10 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-2xs transition-colors hover:border-slate-300 focus:outline-none focus-visible:border-indigo-500 focus-visible:ring-2 focus-visible:ring-indigo-500/25"
      />
      <div className="flex flex-wrap items-center justify-between gap-2">
        <select
          aria-label="Mention a member"
          value=""
          onChange={(e) => handleMention(e.target.value)}
          className="min-h-8 rounded-lg border border-slate-200 bg-white px-2.5 text-xs font-medium text-slate-700 shadow-2xs hover:border-slate-300 focus:outline-none focus-visible:border-indigo-500 focus-visible:ring-2 focus-visible:ring-indigo-500/25"
        >
          <option value="">Mention…</option>
          {members.map((member) => (
            <option key={member.userId} value={member.userId}>
              {member.displayName}
            </option>
          ))}
        </select>
        <div className="flex gap-2">
          {onCancelEvent ? (
            <BaseButton
              variant="secondary"
              size="sm"
              onClick={onCancelEvent}
            >
              Cancel
            </BaseButton>
          ) : null}
          <BaseButton type="submit" size="sm" isLoading={isBusy}>
            {submitLabel}
          </BaseButton>
        </div>
      </div>
    </form>
  );
}

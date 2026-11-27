import type { CSSProperties, HTMLAttributes, Ref } from "react";
import type { Card } from "@/types/api";

interface CardItemProps {
  card: Card;
  itemRef?: Ref<HTMLLIElement>;
  style?: CSSProperties;
  isDragging?: boolean;
  isOverlay?: boolean;
  dragProps?: HTMLAttributes<HTMLLIElement>;
  onCardOpen?: (cardId: string) => void;
}

function getDueDateTone(dueDate: string): string {
  const today = new Date();
  const yyyy = today.getFullYear();
  const mm = String(today.getMonth() + 1).padStart(2, "0");
  const dd = String(today.getDate()).padStart(2, "0");
  const todayStr = `${yyyy}-${mm}-${dd}`;
  if (dueDate < todayStr) {
    return "bg-rose-50 text-rose-700 ring-1 ring-rose-200/80";
  }
  if (dueDate === todayStr) {
    return "bg-amber-50 text-amber-700 ring-1 ring-amber-200/80";
  }
  return "bg-slate-100 text-slate-600";
}

export default function CardItem({
  card,
  itemRef,
  style,
  isDragging = false,
  isOverlay = false,
  dragProps,
  onCardOpen,
}: CardItemProps) {
  const hasDescription = card.description.trim().length > 0;
  const hasAssignee = card.assigneeId !== null;
  const hasMetadata = Boolean(card.dueDate) || hasDescription || hasAssignee;

  return (
    <li
      {...dragProps}
      ref={itemRef}
      style={style}
      onClick={() => onCardOpen?.(card.id)}
      data-testid="card-item"
      className={`group/card rounded-xl border-[1.5px] p-3.5 text-sm text-slate-900 transition duration-150 ${
        isOverlay
          ? "rotate-1 cursor-grabbing list-none border-indigo-300 bg-white shadow-xl ring-2 ring-indigo-500/20"
          : isDragging
            ? "border-dashed border-indigo-300 bg-slate-50 opacity-40 shadow-none"
            : "border-[#211621]/70 bg-[#fffdf7] shadow-[2px_2px_0_#211621] hover:-translate-y-0.5 hover:border-[#211621] hover:shadow-[4px_4px_0_#211621]"
      } ${dragProps ? "cursor-grab touch-manipulation" : "cursor-pointer"}`}
    >
      <p className="text-[13.5px] leading-snug font-medium break-words text-slate-900">
        {card.title}
      </p>
      {hasMetadata ? (
        <div className="mt-2.5 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-500">
          <div className="flex flex-wrap items-center gap-1.5">
            {card.dueDate ? (
              <span
                className={`inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 font-medium tabular-nums ${getDueDateTone(card.dueDate)}`}
              >
                <svg
                  aria-hidden="true"
                  viewBox="0 0 16 16"
                  fill="currentColor"
                  className="size-3 opacity-80"
                >
                  <path
                    fillRule="evenodd"
                    d="M4 1.75a.75.75 0 0 1 1.5 0V3h5V1.75a.75.75 0 0 1 1.5 0V3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2V1.75ZM4.5 6a.5.5 0 0 0 0 1h7a.5.5 0 0 0 0-1h-7Z"
                    clipRule="evenodd"
                  />
                </svg>
                Due {card.dueDate}
              </span>
            ) : null}
            {hasDescription ? (
              <span
                aria-label="Has description"
                title="Has description"
                className="inline-flex items-center text-slate-400"
              >
                <svg
                  aria-hidden="true"
                  viewBox="0 0 16 16"
                  fill="currentColor"
                  className="size-3.5"
                >
                  <path
                    fillRule="evenodd"
                    d="M2 3.75A.75.75 0 0 1 2.75 3h10.5a.75.75 0 0 1 0 1.5H2.75A.75.75 0 0 1 2 3.75Zm0 4A.75.75 0 0 1 2.75 7h10.5a.75.75 0 0 1 0 1.5H2.75A.75.75 0 0 1 2 7.75Zm0 4a.75.75 0 0 1 .75-.75h6.5a.75.75 0 0 1 0 1.5h-6.5a.75.75 0 0 1-.75-.75Z"
                    clipRule="evenodd"
                  />
                </svg>
              </span>
            ) : null}
          </div>
          {hasAssignee ? (
            <span
              aria-label="Assigned"
              title="Assigned"
              className="inline-flex size-5 items-center justify-center rounded-full bg-indigo-50 text-indigo-600 ring-1 ring-indigo-200/70"
            >
              <svg
                aria-hidden="true"
                viewBox="0 0 16 16"
                fill="currentColor"
                className="size-3"
              >
                <path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM12.735 14c.618 0 1.093-.561.872-1.139a6.002 6.002 0 0 0-11.215 0c-.22.578.254 1.139.872 1.139h9.47Z" />
              </svg>
            </span>
          ) : null}
        </div>
      ) : null}
    </li>
  );
}

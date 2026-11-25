import type { CSSProperties, HTMLAttributes, Ref } from "react";
import type { Card } from "@/types/api";

interface CardItemProps {
  card: Card;
  itemRef?: Ref<HTMLLIElement>;
  style?: CSSProperties;
  isDragging?: boolean;
  dragProps?: HTMLAttributes<HTMLLIElement>;
  onCardOpen?: (cardId: string) => void;
}

export default function CardItem({
  card,
  itemRef,
  style,
  isDragging = false,
  dragProps,
  onCardOpen,
}: CardItemProps) {
  return (
    <li
      {...dragProps}
      ref={itemRef}
      style={style}
      onClick={() => onCardOpen?.(card.id)}
      data-testid="card-item"
      className={`rounded-md border border-gray-200 bg-white p-3 text-sm text-gray-900 shadow-sm ${
        dragProps ? "cursor-grab touch-manipulation" : ""
      } ${isDragging ? "opacity-50" : ""}`}
    >
      <p className="font-medium break-words">{card.title}</p>
      {card.dueDate ? (
        <p className="mt-1 text-xs text-gray-600">Due {card.dueDate}</p>
      ) : null}
    </li>
  );
}

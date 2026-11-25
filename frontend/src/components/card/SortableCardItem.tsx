"use client";

import { useSortable } from "@dnd-kit/sortable";
import CardItem from "@/components/card/CardItem";
import type { Card } from "@/types/api";

interface SortableCardItemProps {
  card: Card;
  onCardOpen: (cardId: string) => void;
}

export default function SortableCardItem({
  card,
  onCardOpen,
}: SortableCardItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: card.id });

  return (
    <CardItem
      card={card}
      onCardOpen={onCardOpen}
      itemRef={setNodeRef}
      style={{
        transform: transform
          ? `translate3d(${Math.round(transform.x)}px, ${Math.round(transform.y)}px, 0)`
          : undefined,
        transition,
      }}
      isDragging={isDragging}
      dragProps={{ ...attributes, ...listeners }}
    />
  );
}

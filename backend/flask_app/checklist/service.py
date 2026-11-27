from typing import Any
from uuid import UUID

from sqlalchemy import func, select

from flask_app.common.exceptions import NotFoundError, ValidationError
from flask_app.extensions import db
from flask_app.models import Card, ChecklistItem

MAX_CHECKLIST_ITEMS = 50


def checklist_item_dict(item: ChecklistItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "card_id": item.card_id,
        "text": item.text,
        "is_done": item.is_done,
        "order_index": item.order_index,
        "created_at": item.created_at,
    }


def _get_item(item_id: UUID) -> ChecklistItem:
    item = db.session.get(ChecklistItem, item_id)
    if item is None:
        raise NotFoundError("To-do item not found")
    return item


def create_checklist_item_service(card_id: UUID, payload: dict[str, Any]) -> dict[str, Any]:
    """Append an item to the Card's to-do list. Does not touch the Card's version."""
    # Lock the Card row so two concurrent adds cannot pass the limit together.
    card = db.session.scalar(select(Card).where(Card.id == card_id).with_for_update())
    if card is None:
        raise NotFoundError("Card not found")
    count, last_index = db.session.execute(
        select(func.count(), func.max(ChecklistItem.order_index)).where(
            ChecklistItem.card_id == card_id
        )
    ).one()
    if count >= MAX_CHECKLIST_ITEMS:
        raise ValidationError(
            f"A Card can have at most {MAX_CHECKLIST_ITEMS} to-do items", field="text"
        )
    item = ChecklistItem(
        card_id=card_id,
        text=payload["text"],
        is_done=False,
        order_index=0 if last_index is None else last_index + 1,
    )
    db.session.add(item)
    db.session.commit()
    return checklist_item_dict(item)


def update_checklist_item_service(item_id: UUID, payload: dict[str, Any]) -> dict[str, Any]:
    """Edit the text and/or the done state; omitted fields stay unchanged."""
    if "text" not in payload and "is_done" not in payload:
        raise ValidationError("Provide text or isDone")
    item = _get_item(item_id)
    if "text" in payload:
        item.text = payload["text"]
    if "is_done" in payload:
        item.is_done = payload["is_done"]
    db.session.commit()
    return checklist_item_dict(item)


def delete_checklist_item_service(item_id: UUID) -> None:
    db.session.delete(_get_item(item_id))
    db.session.commit()

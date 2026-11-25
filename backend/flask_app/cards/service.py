from typing import Any
from uuid import UUID

from sqlalchemy import select, update

from flask_app.activity.service import record_activity
from flask_app.common.exceptions import ConflictError, NotFoundError, ValidationError
from flask_app.common.ordering import reindex
from flask_app.common.time import utc_now
from flask_app.extensions import db
from flask_app.models import BoardMembership, Card, Column, User

_EDITABLE_FIELDS = ("title", "description", "assignee_id", "due_date")


def _card_dict(card: Card) -> dict[str, Any]:
    return {
        "id": card.id,
        "column_id": card.column_id,
        "board_id": card.board_id,
        "title": card.title,
        "description": card.description,
        "assignee_id": card.assignee_id,
        "due_date": card.due_date,
        "created_by_id": card.created_by_id,
        "order_index": card.order_index,
        "version": card.version,
        "created_at": card.created_at,
        "updated_at": card.updated_at,
    }


def _get_card(card_id: UUID) -> Card:
    card = db.session.get(Card, card_id)
    if card is None:
        raise NotFoundError("Card not found")
    return card


def _lock_column_cards(column_id: UUID) -> list[Card]:
    """Lock and return the Column's Cards in order."""
    query = (
        select(Card)
        .where(Card.column_id == column_id)
        .order_by(Card.order_index, Card.id)
        .with_for_update()
    )
    return list(db.session.scalars(query))


def _validate_assignee(board_id: UUID, assignee_id: UUID | None) -> None:
    if assignee_id is None:
        return
    is_member = db.session.scalar(
        select(BoardMembership.id).where(
            BoardMembership.board_id == board_id, BoardMembership.user_id == assignee_id
        )
    )
    if is_member is None:
        raise ValidationError("Assignee must be a member of the Board", field="assignee_id")


def create_card_service(column_id: UUID, payload: dict[str, Any], user: User) -> dict[str, Any]:
    column = db.session.get(Column, column_id)
    if column is None:
        raise NotFoundError("Column not found")
    assignee_id: UUID | None = payload.get("assignee_id")
    _validate_assignee(column.board_id, assignee_id)
    cards = _lock_column_cards(column_id)
    now = utc_now()
    card = Card(
        column_id=column_id,
        board_id=column.board_id,
        title=payload["title"],
        description=payload.get("description", ""),
        assignee_id=assignee_id,
        due_date=payload.get("due_date"),
        created_by_id=user.id,
        order_index=len(cards),
        version=1,
        created_at=now,
        updated_at=now,
    )
    db.session.add(card)
    db.session.flush()
    record_activity(column.board_id, user.id, "card_created", card.id)
    db.session.commit()
    return _card_dict(card)


def get_card_service(card_id: UUID) -> dict[str, Any]:
    return _card_dict(_get_card(card_id))


def update_card_service(card_id: UUID, payload: dict[str, Any], user: User) -> dict[str, Any]:
    card = _get_card(card_id)
    changes = {name: payload[name] for name in _EDITABLE_FIELDS if name in payload}
    if "assignee_id" in changes:
        _validate_assignee(card.board_id, changes["assignee_id"])
    expected = payload.get("version")
    if expected is None:
        raise ConflictError("Card version is required")
    result = db.session.execute(
        update(Card)
        .where(Card.id == card_id, Card.version == expected)
        .values(**changes, updated_at=utc_now(), version=expected + 1)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount == 0:  # type: ignore[attr-defined]
        raise ConflictError("Card was modified by someone else; reload and retry")
    db.session.refresh(card)
    record_activity(card.board_id, user.id, "card_updated", card.id)
    db.session.commit()
    return _card_dict(card)


def move_card_service(
    card_id: UUID, target_column_id: UUID, target_index: int, actor: User
) -> dict[str, Any]:
    card = _get_card(card_id)
    target = db.session.get(Column, target_column_id)
    if target is None or target.board_id != card.board_id:
        raise ValidationError(
            "Target column must belong to the same Board", field="target_column_id"
        )
    if isinstance(target_index, bool) or not isinstance(target_index, int):
        raise ValidationError("Target index must be an integer", field="target_index")
    source_id = card.column_id
    # Lock affected Column rows in a stable order so concurrent moves cannot deadlock.
    column_ids = sorted({source_id, target_column_id})
    db.session.execute(
        select(Column.id).where(Column.id.in_(column_ids)).order_by(Column.id).with_for_update()
    )
    source_cards = _lock_column_cards(source_id)
    source_cards.remove(card)
    target_cards = (
        source_cards if target_column_id == source_id else _lock_column_cards(target_column_id)
    )
    if not 0 <= target_index <= len(target_cards):
        raise ValidationError("Target index is out of range", field="target_index")
    target_cards.insert(target_index, card)
    card.column_id = target_column_id
    card.updated_at = utc_now()
    reindex(source_cards)
    reindex(target_cards)
    record_activity(card.board_id, actor.id, "card_moved", card.id)
    db.session.commit()
    return _card_dict(card)


def delete_card_service(card_id: UUID, user: User) -> None:
    card = _get_card(card_id)
    board_id = card.board_id
    cards = _lock_column_cards(card.column_id)
    cards.remove(card)
    db.session.delete(card)
    reindex(cards)
    record_activity(board_id, user.id, "card_deleted", card_id)
    db.session.commit()

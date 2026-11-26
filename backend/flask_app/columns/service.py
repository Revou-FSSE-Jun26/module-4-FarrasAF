from typing import Any
from uuid import UUID

from sqlalchemy import func, select

from flask_app.activity.service import record_activity
from flask_app.common.exceptions import NotFoundError, ValidationError
from flask_app.common.ordering import reindex
from flask_app.extensions import db
from flask_app.models import Board, Card, Column, User


def _column_dict(column: Column) -> dict[str, Any]:
    return {
        "id": column.id,
        "board_id": column.board_id,
        "name": column.name,
        "order_index": column.order_index,
    }


def list_board_columns_service(board_id: UUID) -> list[dict[str, Any]]:
    """Return the Board's Columns in order, each with its ordered Cards nested."""
    from flask_app.cards.service import _card_dict

    columns = list(
        db.session.scalars(
            select(Column)
            .where(Column.board_id == board_id)
            .order_by(Column.order_index, Column.id)
        )
    )
    cards = db.session.scalars(
        select(Card).where(Card.board_id == board_id).order_by(Card.order_index, Card.id)
    )
    by_column: dict[UUID, list[dict[str, Any]]] = {column.id: [] for column in columns}
    for card in cards:
        by_column.setdefault(card.column_id, []).append(_card_dict(card))
    return [
        {**_column_dict(column), "created_at": column.created_at, "cards": by_column[column.id]}
        for column in columns
    ]


def _lock_board_columns(board_id: UUID) -> list[Column]:
    """Lock and return the Board's Columns in order."""
    query = (
        select(Column)
        .where(Column.board_id == board_id)
        .order_by(Column.order_index, Column.id)
        .with_for_update()
    )
    return list(db.session.scalars(query))


def _get_column(column_id: UUID) -> Column:
    column = db.session.get(Column, column_id)
    if column is None:
        raise NotFoundError("Column not found")
    return column


def create_column_service(board_id: UUID, payload: dict[str, Any], user: User) -> dict[str, Any]:
    if db.session.get(Board, board_id) is None:
        raise NotFoundError("Board not found")
    columns = _lock_board_columns(board_id)
    column = Column(board_id=board_id, name=payload["name"], order_index=len(columns))
    db.session.add(column)
    db.session.flush()
    record_activity(board_id, user.id, "column_created", column.id)
    db.session.commit()
    return _column_dict(column)


def rename_column_service(column_id: UUID, payload: dict[str, Any]) -> dict[str, Any]:
    column = _get_column(column_id)
    column.name = payload["name"]
    db.session.commit()
    return _column_dict(column)


def reorder_column_service(column_id: UUID, payload: dict[str, Any]) -> dict[str, Any]:
    column = _get_column(column_id)
    columns = _lock_board_columns(column.board_id)
    target_index: int = payload["target_index"]
    if not 0 <= target_index < len(columns):
        raise ValidationError("Target index is out of range", field="target_index")
    columns.remove(column)
    columns.insert(target_index, column)
    reindex(columns)
    db.session.commit()
    return _column_dict(column)


def delete_column_service(column_id: UUID, user: User) -> None:
    column = _get_column(column_id)
    board_id = column.board_id
    columns = _lock_board_columns(board_id)
    card_count = db.session.scalar(
        select(func.count()).select_from(Card).where(Card.column_id == column_id)
    )
    if card_count:
        raise ValidationError("Column must be empty before it can be deleted")
    columns.remove(column)
    db.session.delete(column)
    reindex(columns)
    record_activity(board_id, user.id, "column_deleted", column_id)
    db.session.commit()

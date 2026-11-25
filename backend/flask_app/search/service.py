from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from flask_app.common.pagination import SEARCH_PAGE_SIZE
from flask_app.extensions import db
from flask_app.models import BoardMembership, Card, User


def escape_like(keyword: str) -> str:
    """Escape `\\`, `%` and `_` so the keyword is matched as a literal substring."""
    return keyword.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _result_dict(card: Card) -> dict[str, Any]:
    return {
        "id": card.id,
        "title": card.title,
        "description": card.description,
        "assignee_id": card.assignee_id,
        "due_date": card.due_date,
        "order_index": card.order_index,
        "created_at": card.created_at,
        "updated_at": card.updated_at,
        "board": {"id": card.board.id, "name": card.board.name},
        "column": {"id": card.column.id, "name": card.column.name},
    }


def search_cards_service(user: User, payload: dict[str, Any]) -> dict[str, Any]:
    """Cards whose Title contains `q` (case-insensitive, literal) on the user's Boards.

    Archived Boards stay included: Board access comes from membership only.
    """
    pattern = f"%{escape_like(payload['q'])}%"
    accessible = select(BoardMembership.board_id).where(BoardMembership.user_id == user.id)
    query = (
        select(Card)
        .where(Card.board_id.in_(accessible), Card.title.ilike(pattern, escape="\\"))
        .options(
            joinedload(Card.board),  # type: ignore[arg-type]
            joinedload(Card.column),  # type: ignore[arg-type]
        )
        .order_by(Card.updated_at.desc(), Card.id.desc())
        .limit(SEARCH_PAGE_SIZE)
    )
    cards = db.session.scalars(query).all()
    return {"items": [_result_dict(card) for card in cards]}

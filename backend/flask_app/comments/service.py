import re
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import joinedload

from flask_app.activity.service import record_activity
from flask_app.common.exceptions import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from flask_app.common.time import utc_now
from flask_app.extensions import db
from flask_app.models import BoardMembership, Card, Comment, Notification, User

_MENTION_PATTERN = re.compile(r"@\[([0-9a-fA-F-]{36})\]")


def parse_mentions(body: str) -> list[UUID]:
    """Distinct valid UUIDs from `@[<uuid>]` tokens, in order of first appearance."""
    seen: dict[UUID, None] = {}
    for token in _MENTION_PATTERN.findall(body):
        try:
            seen.setdefault(UUID(token), None)
        except ValueError:
            continue
    return list(seen)


def _comment_dict(comment: Comment) -> dict[str, Any]:
    return {
        "id": comment.id,
        "card_id": comment.card_id,
        "author_id": comment.author_id,
        "parent_comment_id": comment.parent_comment_id,
        "body": comment.body,
        "edited_at": comment.edited_at,
        "version": comment.version,
        "created_at": comment.created_at,
    }


def _get_card(card_id: UUID) -> Card:
    card = db.session.get(Card, card_id)
    if card is None:
        raise NotFoundError("Card not found")
    return card


def _get_comment(comment_id: UUID) -> Comment:
    comment = db.session.get(Comment, comment_id)
    if comment is None:
        raise NotFoundError("Comment not found")
    return comment


def _require_author(comment: Comment, user: User) -> None:
    if comment.author_id != user.id:
        raise AuthorizationError("Only the author can change this Comment")


def list_comments_service(card_id: UUID) -> dict[str, Any]:
    _get_card(card_id)
    query = (
        select(Comment)
        .options(joinedload(Comment.author))  # type: ignore[arg-type]
        .where(Comment.card_id == card_id)
        .order_by(Comment.created_at, Comment.id)
    )
    return {"items": [_comment_dict(c) for c in db.session.scalars(query).all()]}


def create_comment_service(card_id: UUID, payload: dict[str, Any], user: User) -> dict[str, Any]:
    card = _get_card(card_id)
    parent_id: UUID | None = payload.get("parent_comment_id")
    if parent_id is not None:
        parent = db.session.get(Comment, parent_id)
        if parent is None or parent.card_id != card_id:
            raise ValidationError(
                "Parent Comment must exist on the same Card", field="parent_comment_id"
            )
    comment = Comment(
        card_id=card_id,
        author_id=user.id,
        parent_comment_id=parent_id,
        body=payload["body"],
        version=1,
    )
    db.session.add(comment)
    db.session.flush()
    mentioned = parse_mentions(comment.body)
    if mentioned:
        member_ids = db.session.scalars(
            select(BoardMembership.user_id).where(
                BoardMembership.board_id == card.board_id,
                BoardMembership.user_id.in_(mentioned),
            )
        ).all()
        for recipient_id in member_ids:
            db.session.add(
                Notification(
                    recipient_id=recipient_id,
                    comment_id=comment.id,
                    board_id=card.board_id,
                    status="unread",
                )
            )
    record_activity(
        card.board_id,
        user.id,
        "comment_created",
        comment.id,
        card_id,
        details={"card_title": card.title},
    )
    db.session.commit()
    return _comment_dict(comment)


def update_comment_service(comment_id: UUID, payload: dict[str, Any], user: User) -> dict[str, Any]:
    comment = _get_comment(comment_id)
    _require_author(comment, user)
    expected = payload.get("version")
    if expected is None:
        raise ConflictError("Comment version is required")
    result = db.session.execute(
        update(Comment)
        .where(Comment.id == comment_id, Comment.version == expected)
        .values(body=payload["body"], edited_at=utc_now(), version=expected + 1)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount == 0:  # type: ignore[attr-defined]
        raise ConflictError("Comment was modified by someone else; reload and retry")
    db.session.refresh(comment)
    card = _get_card(comment.card_id)
    record_activity(
        card.board_id,
        user.id,
        "comment_edited",
        comment.id,
        comment.card_id,
        details={"card_title": card.title},
    )
    db.session.commit()
    return _comment_dict(comment)


def delete_comment_service(comment_id: UUID, user: User) -> None:
    comment = _get_comment(comment_id)
    _require_author(comment, user)
    card_id = comment.card_id
    card = _get_card(card_id)
    # Replies and their Notifications are removed by the database ON DELETE CASCADE.
    db.session.delete(comment)
    record_activity(
        card.board_id,
        user.id,
        "comment_deleted",
        comment_id,
        card_id,
        details={"card_title": card.title},
    )
    db.session.commit()

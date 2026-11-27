from collections.abc import Iterable
from typing import Any
from uuid import UUID

from sqlalchemy import select, tuple_
from sqlalchemy.orm import joinedload

from flask_app.common.cursor import decode_cursor, encode_cursor
from flask_app.common.exceptions import AuthorizationError, NotFoundError
from flask_app.common.pagination import NOTIFICATIONS_PAGE_SIZE
from flask_app.extensions import db
from flask_app.models import BoardMembership, Comment, Notification, User


def create_mention_notifications(
    comment_id: UUID, board_id: UUID, mentioned_user_ids: Iterable[UUID]
) -> list[Notification]:
    """Add one unread Notification per distinct mentioned current Board Member.

    Never commits; the caller owns the transaction. Other ids are ignored.
    """
    distinct = set(mentioned_user_ids)
    if not distinct:
        return []
    member_ids = set(
        db.session.scalars(
            select(BoardMembership.user_id).where(
                BoardMembership.board_id == board_id,
                BoardMembership.user_id.in_(distinct),
            )
        )
    )
    created = [
        Notification(
            recipient_id=user_id,
            type="comment_mention",
            comment_id=comment_id,
            board_id=board_id,
            status="unread",
        )
        for user_id in sorted(member_ids, key=str)
    ]
    db.session.add_all(created)
    return created


def should_notify_assignment(
    previous_assignee_id: UUID | None, new_assignee_id: UUID | None, actor_id: UUID
) -> bool:
    """Pure rule (R6.11 to R6.13): notify only a new, different Assignee who is not the actor."""
    if new_assignee_id is None or new_assignee_id == previous_assignee_id:
        return False
    return new_assignee_id != actor_id


def create_assignment_notification(
    card_id: UUID,
    board_id: UUID,
    previous_assignee_id: UUID | None,
    new_assignee_id: UUID | None,
    actor_id: UUID,
) -> Notification | None:
    """Add one unread "card assigned" Notification when the rule applies.

    Never commits; the caller owns the transaction.
    """
    if new_assignee_id is None or not should_notify_assignment(
        previous_assignee_id, new_assignee_id, actor_id
    ):
        return None
    notification = Notification(
        recipient_id=new_assignee_id,
        type="card_assigned",
        card_id=card_id,
        board_id=board_id,
        status="unread",
    )
    db.session.add(notification)
    return notification


def _notification_to_dict(notification: Notification) -> dict[str, Any]:
    card = notification.card
    if card is None and notification.comment is not None:
        # comment_mention: the Card is the one the Comment belongs to (R6.15)
        card = notification.comment.card
    return {
        "id": notification.id,
        "recipient_id": notification.recipient_id,
        "type": notification.type,
        "comment_id": notification.comment_id,
        "card_id": notification.card_id,
        "card_title": card.title if card is not None else None,
        "board_id": notification.board_id,
        "board_name": notification.board.name,
        "status": notification.status,
        "created_at": notification.created_at,
    }


def list_notifications_service(user: User, payload: dict[str, Any]) -> dict[str, Any]:
    """Newest-first page of the user's Notifications; malformed cursor raises ValidationError."""
    cursor: str | None = payload.get("cursor")
    unread_only: bool = payload.get("unread_only", False)
    query = (
        select(Notification)
        .options(
            joinedload(Notification.card),  # type: ignore[arg-type]
            joinedload(Notification.comment).joinedload(Comment.card),  # type: ignore[arg-type]
            joinedload(Notification.board),  # type: ignore[arg-type]
        )
        .where(Notification.recipient_id == user.id)
    )
    if unread_only:
        query = query.where(Notification.status == "unread")
    if cursor is not None:
        created_at, last_id = decode_cursor(cursor)
        query = query.where(
            tuple_(Notification.created_at, Notification.id) < tuple_(created_at, last_id)
        )
    query = query.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(
        NOTIFICATIONS_PAGE_SIZE + 1
    )
    rows = list(db.session.scalars(query))
    has_more = len(rows) > NOTIFICATIONS_PAGE_SIZE
    page = rows[:NOTIFICATIONS_PAGE_SIZE]
    next_cursor = encode_cursor(page[-1].created_at, page[-1].id) if has_more else None
    return {"items": [_notification_to_dict(n) for n in page], "next_cursor": next_cursor}


def mark_notification_read_service(notification_id: UUID, user: User) -> dict[str, Any]:
    """Mark the user's own Notification as read; anyone else gets AuthorizationError."""
    notification = db.session.get(Notification, notification_id)
    if notification is None:
        raise NotFoundError("Notification not found")
    if notification.recipient_id != user.id:
        raise AuthorizationError("You cannot modify this notification")
    notification.status = "read"
    db.session.commit()
    return _notification_to_dict(notification)

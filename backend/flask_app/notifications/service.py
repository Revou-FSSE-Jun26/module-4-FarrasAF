from collections.abc import Iterable
from typing import Any
from uuid import UUID

from sqlalchemy import select, tuple_

from flask_app.common.cursor import decode_cursor, encode_cursor
from flask_app.common.exceptions import AuthorizationError, NotFoundError
from flask_app.common.pagination import NOTIFICATIONS_PAGE_SIZE
from flask_app.extensions import db
from flask_app.models import BoardMembership, Notification, User


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
            recipient_id=user_id, comment_id=comment_id, board_id=board_id, status="unread"
        )
        for user_id in sorted(member_ids, key=str)
    ]
    db.session.add_all(created)
    return created


def _notification_to_dict(notification: Notification) -> dict[str, Any]:
    return {
        "id": notification.id,
        "comment_id": notification.comment_id,
        "board_id": notification.board_id,
        "status": notification.status,
        "created_at": notification.created_at,
    }


def list_notifications_service(user: User, payload: dict[str, Any]) -> dict[str, Any]:
    """Newest-first page of the user's Notifications; malformed cursor raises ValidationError."""
    cursor: str | None = payload.get("cursor")
    unread_only: bool = payload.get("unread_only", False)
    query = select(Notification).where(Notification.recipient_id == user.id)
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

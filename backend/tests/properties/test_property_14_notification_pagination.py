"""Property 14: Notification cursor pagination visits each notification exactly once in order.

**Validates: Requirements 6.2, 6.3, 6.4, 6.6, 6.7**
"""

import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from flask_app.common.cursor import encode_cursor
from flask_app.common.pagination import NOTIFICATIONS_PAGE_SIZE
from flask_app.notifications.service import list_notifications_service

from flask_app.models import Card, Comment, Notification, User  # isort: skip

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)

_BASE = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)

# (timestamp slot, is_unread). Few slots force many created_at ties.
_ITEMS = st.tuples(st.integers(0, 6), st.booleans())

MakeUser = Callable[..., User]


def _add_notifications(
    db_session: Any,
    card: Card,
    recipient: User,
    author: User,
    items: list[tuple[int, bool]],
) -> list[Notification]:
    comments = [Comment(card_id=card.id, author_id=author.id, body="c") for _ in items]
    db_session.add_all(comments)
    db_session.flush()
    notes = [
        Notification(
            recipient_id=recipient.id,
            comment_id=comment.id,
            board_id=card.board_id,
            status="unread" if unread else "read",
            created_at=_BASE + timedelta(minutes=slot),
        )
        for comment, (slot, unread) in zip(comments, items, strict=True)
    ]
    db_session.add_all(notes)
    db_session.flush()
    return notes


def _walk(user: User, unread_only: bool) -> list[dict[str, Any]]:
    """Follow next_cursor to the end, checking per-page invariants."""
    pages: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        payload: dict[str, Any] = {"unread_only": unread_only}
        if cursor is not None:
            payload["cursor"] = cursor
        page = list_notifications_service(user, payload)
        pages.append(page)
        cursor = page["next_cursor"]
        if cursor is None:
            return pages
        assert len(pages) < 10, "pagination did not terminate"


# Feature: task-management-app, Property 14: Notification cursor pagination visits each notification exactly once in order  # noqa: E501
@_SETTINGS
@given(
    mine=st.lists(_ITEMS, max_size=130),
    others=st.lists(_ITEMS, max_size=15),
    unread_only=st.booleans(),
)
def test_notification_pagination_visits_each_once_in_order(
    db_session: Any,
    make_user: MakeUser,
    make_card: Callable[..., Card],
    mine: list[tuple[int, bool]],
    others: list[tuple[int, bool]],
    unread_only: bool,
) -> None:
    recipient = make_user()
    other_user = make_user()
    card = make_card()
    mine_rows = _add_notifications(db_session, card, recipient, other_user, mine)
    other_rows = _add_notifications(db_session, card, other_user, recipient, others)

    candidates = [n for n in mine_rows if not unread_only or n.status == "unread"]
    expected = sorted(candidates, key=lambda n: (n.created_at, n.id), reverse=True)
    expected_ids = [n.id for n in expected]

    pages = _walk(recipient, unread_only)

    visited: list[uuid.UUID] = [item["id"] for page in pages for item in page["items"]]
    # Each notification exactly once, newest first (created_at desc, id desc).
    assert visited == expected_ids
    # Only the recipient's notifications, and only unread when filtered.
    assert not set(visited) & {n.id for n in other_rows}
    if unread_only:
        assert all(item["status"] == "unread" for page in pages for item in page["items"])

    seen = 0
    for index, page in enumerate(pages):
        items = page["items"]
        assert len(items) <= NOTIFICATIONS_PAGE_SIZE
        seen += len(items)
        is_last = index == len(pages) - 1
        if is_last:
            assert page["next_cursor"] is None
            assert seen == len(expected)
        else:
            # Non-final pages are full and carry the cursor of their last item.
            assert len(items) == NOTIFICATIONS_PAGE_SIZE
            last = items[-1]
            assert page["next_cursor"] == encode_cursor(last["created_at"], last["id"])
            # Strictly after the cursor: the next page starts after this page's last item.
            first_next = pages[index + 1]["items"][0]
            assert (first_next["created_at"], first_next["id"]) < (last["created_at"], last["id"])

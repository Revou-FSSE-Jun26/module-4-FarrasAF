"""Unit tests for the notifications module (R6.1-R6.10)."""

import uuid
from collections.abc import Callable
from typing import Any

import pytest
from sqlalchemy import select

from flask_app.cards.service import (
    create_card_service,
    delete_card_service,
    move_card_service,
    update_card_service,
)
from flask_app.common.exceptions import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from flask_app.common.pagination import NOTIFICATIONS_PAGE_SIZE
from flask_app.common.validation import load_schema
from flask_app.extensions import db
from flask_app.models import BoardMembership, Card, Comment, Notification, User
from flask_app.notifications.schema import NotificationsQuerySchema
from flask_app.notifications.service import (
    create_mention_notifications,
    list_notifications_service,
    mark_notification_read_service,
    should_notify_assignment,
)
from tests.conftest import FakeClock


@pytest.fixture
def comment(
    db_session: Any, make_user: Callable[..., User], make_card: Callable[..., Card]
) -> Comment:
    author = make_user()
    card = make_card(created_by=author)
    item = Comment(card_id=card.id, author_id=author.id, body="hi")
    db_session.add(item)
    db_session.flush()
    return item


def _add_member(db_session: Any, board_id: uuid.UUID, user: User) -> None:
    db_session.add(BoardMembership(board_id=board_id, user_id=user.id, role="member"))
    db_session.flush()


def _seed(db_session: Any, comment: Comment, board_id: uuid.UUID, user: User) -> Notification:
    n = Notification(recipient_id=user.id, comment_id=comment.id, board_id=board_id)
    db_session.add(n)
    db_session.flush()
    return n


def test_create_mention_notifications_only_distinct_board_members(
    db_session: Any, make_user: Callable[..., User], comment: Comment
) -> None:
    board_id = comment.card.board_id
    member, outsider = make_user(), make_user()
    _add_member(db_session, board_id, member)
    created = create_mention_notifications(
        comment.id, board_id, [member.id, member.id, outsider.id, uuid.uuid4()]
    )
    db_session.flush()
    assert [(n.recipient_id, n.status) for n in created] == [(member.id, "unread")]
    assert db_session.query(Notification).count() == 1


def test_create_mention_notifications_empty_adds_nothing(db_session: Any, comment: Comment) -> None:
    assert create_mention_notifications(comment.id, comment.card.board_id, []) == []


def test_list_paginates_newest_first_with_cursor(
    db_session: Any, clock: FakeClock, make_user: Callable[..., User], comment: Comment
) -> None:
    user, other = make_user(), make_user()
    board_id = comment.card.board_id
    ids = []
    for _ in range(NOTIFICATIONS_PAGE_SIZE + 3):
        clock.advance(seconds=1)
        item = Comment(card_id=comment.card_id, author_id=comment.author_id, body="x")
        db_session.add(item)
        db_session.flush()
        ids.append(_seed(db_session, item, board_id, user).id)
    _seed(db_session, comment, board_id, other)

    first = list_notifications_service(user, {})
    assert [i["id"] for i in first["items"]] == ids[::-1][:NOTIFICATIONS_PAGE_SIZE]
    assert first["next_cursor"] is not None
    second = list_notifications_service(user, {"cursor": first["next_cursor"]})
    assert [i["id"] for i in second["items"]] == ids[::-1][NOTIFICATIONS_PAGE_SIZE:]
    assert second["next_cursor"] is None


def test_list_unread_only_filter(
    db_session: Any, make_user: Callable[..., User], comment: Comment
) -> None:
    user = make_user()
    board_id = comment.card.board_id
    read = _seed(db_session, comment, board_id, user)
    read.status = "read"
    other_comment = Comment(card_id=comment.card_id, author_id=comment.author_id, body="y")
    db_session.add(other_comment)
    db_session.flush()
    unread = _seed(db_session, other_comment, board_id, user)
    result = list_notifications_service(user, {"unread_only": True})
    assert [i["id"] for i in result["items"]] == [unread.id]
    assert len(list_notifications_service(user, {})["items"]) == 2


def test_list_malformed_cursor_raises_validation_error(
    db_session: Any, make_user: Callable[..., User], comment: Comment
) -> None:
    user = make_user()
    _seed(db_session, comment, comment.card.board_id, user)
    for bad in ("not-a-cursor!", "", "e30"):
        with pytest.raises(ValidationError):
            list_notifications_service(user, {"cursor": bad})


def test_mark_read_by_recipient(
    db_session: Any, make_user: Callable[..., User], comment: Comment
) -> None:
    user = make_user()
    n = _seed(db_session, comment, comment.card.board_id, user)
    assert mark_notification_read_service(n.id, user)["status"] == "read"
    db.session.refresh(n)
    assert n.status == "read"


def test_mark_read_by_other_user_is_rejected_and_unchanged(
    db_session: Any, make_user: Callable[..., User], comment: Comment
) -> None:
    n = _seed(db_session, comment, comment.card.board_id, make_user())
    with pytest.raises(AuthorizationError):
        mark_notification_read_service(n.id, make_user())
    assert n.status == "unread"


def test_mark_read_unknown_notification(make_user: Callable[..., User]) -> None:
    with pytest.raises(NotFoundError):
        mark_notification_read_service(uuid.uuid4(), make_user())


def test_query_schema() -> None:
    assert load_schema(NotificationsQuerySchema(), {"cursor": "abc", "unread_only": "true"}) == {
        "cursor": "abc",
        "unread_only": True,
    }
    with pytest.raises(ValidationError):
        load_schema(NotificationsQuerySchema(), {"unread_only": "maybe"})
    with pytest.raises(ValidationError):
        load_schema(NotificationsQuerySchema(), {"page": "1"})


# ---- Card assignment Notifications (R6.11 - R6.17) ----


def _assignment_notifications(db_session: Any) -> list[Notification]:
    db_session.expire_all()
    return list(
        db_session.scalars(select(Notification).where(Notification.type == "card_assigned"))
    )


def _board_with_members(
    db_session: Any,
    make_user: Callable[..., User],
    make_board: Callable[..., Any],
    make_column: Callable[..., Any],
) -> tuple[User, User, Any]:
    admin, member = make_user(), make_user()
    board = make_board(admin=admin, name="Roadmap")
    _add_member(db_session, board.id, member)
    return admin, member, make_column(board=board)


def test_should_notify_assignment_rule() -> None:
    a, b, actor = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    assert should_notify_assignment(None, a, actor) is True
    assert should_notify_assignment(a, b, actor) is True
    assert should_notify_assignment(a, a, actor) is False
    assert should_notify_assignment(a, None, actor) is False
    assert should_notify_assignment(None, None, actor) is False
    assert should_notify_assignment(a, actor, actor) is False
    assert should_notify_assignment(None, actor, actor) is False


def test_create_card_with_assignee_notifies_assignee(
    db_session: Any,
    make_user: Callable[..., User],
    make_board: Callable[..., Any],
    make_column: Callable[..., Any],
) -> None:
    admin, member, column = _board_with_members(db_session, make_user, make_board, make_column)
    card = create_card_service(column.id, {"title": "Ship", "assignee_id": member.id}, admin)
    rows = _assignment_notifications(db_session)
    assert [(n.recipient_id, n.card_id, n.board_id, n.status) for n in rows] == [
        (member.id, card["id"], column.board_id, "unread")
    ]
    assert rows[0].comment_id is None


def test_create_card_without_assignee_or_self_assigned_creates_none(
    db_session: Any,
    make_user: Callable[..., User],
    make_board: Callable[..., Any],
    make_column: Callable[..., Any],
) -> None:
    admin, _member, column = _board_with_members(db_session, make_user, make_board, make_column)
    create_card_service(column.id, {"title": "A"}, admin)
    create_card_service(column.id, {"title": "B", "assignee_id": admin.id}, admin)
    assert _assignment_notifications(db_session) == []


def test_update_card_notifies_only_on_new_assignee(
    db_session: Any,
    make_user: Callable[..., User],
    make_board: Callable[..., Any],
    make_column: Callable[..., Any],
) -> None:
    admin, member, column = _board_with_members(db_session, make_user, make_board, make_column)
    other = make_user()
    _add_member(db_session, column.board_id, other)
    card = create_card_service(column.id, {"title": "A"}, admin)
    card_id = card["id"]
    # empty -> member
    update_card_service(card_id, {"assignee_id": member.id, "version": 1}, admin)
    assert len(_assignment_notifications(db_session)) == 1
    # unchanged assignee and other field edits: nothing new
    update_card_service(card_id, {"assignee_id": member.id, "version": 2}, admin)
    update_card_service(card_id, {"title": "A2", "version": 3}, admin)
    assert len(_assignment_notifications(db_session)) == 1
    # removal: nothing new
    update_card_service(card_id, {"assignee_id": None, "version": 4}, admin)
    assert len(_assignment_notifications(db_session)) == 1
    # member -> other
    update_card_service(card_id, {"assignee_id": member.id, "version": 5}, admin)
    update_card_service(card_id, {"assignee_id": other.id, "version": 6}, admin)
    recipients = sorted(str(n.recipient_id) for n in _assignment_notifications(db_session))
    assert recipients == sorted(str(i) for i in (member.id, member.id, other.id))
    # self-assignment by the actor: nothing new
    update_card_service(card_id, {"assignee_id": admin.id, "version": 7}, admin)
    assert len(_assignment_notifications(db_session)) == 3


def test_rejected_edit_creates_no_assignment_notification(
    db_session: Any,
    make_user: Callable[..., User],
    make_board: Callable[..., Any],
    make_column: Callable[..., Any],
) -> None:
    admin, member, column = _board_with_members(db_session, make_user, make_board, make_column)
    card = create_card_service(column.id, {"title": "A"}, admin)
    with pytest.raises(ConflictError):
        update_card_service(card["id"], {"assignee_id": member.id, "version": 99}, admin)
    with pytest.raises(ValidationError):
        update_card_service(card["id"], {"assignee_id": make_user().id, "version": 1}, admin)
    assert _assignment_notifications(db_session) == []


def test_move_card_creates_no_assignment_notification(
    db_session: Any,
    make_user: Callable[..., User],
    make_board: Callable[..., Any],
    make_column: Callable[..., Any],
) -> None:
    admin, member, column = _board_with_members(db_session, make_user, make_board, make_column)
    card = create_card_service(column.id, {"title": "A", "assignee_id": member.id}, admin)
    other_column = make_column(board=column.board, name="Doing")
    move_card_service(card["id"], other_column.id, 0, admin)
    assert len(_assignment_notifications(db_session)) == 1


def test_list_includes_assignment_fields_and_mention_has_null_card(
    db_session: Any,
    make_user: Callable[..., User],
    make_board: Callable[..., Any],
    make_column: Callable[..., Any],
    comment: Comment,
) -> None:
    admin, member, column = _board_with_members(db_session, make_user, make_board, make_column)
    card = create_card_service(column.id, {"title": "Ship", "assignee_id": member.id}, admin)
    _seed(db_session, comment, comment.card.board_id, member)
    items = list_notifications_service(member, {})["items"]
    by_type = {n["type"]: n for n in items}
    assigned = by_type["card_assigned"]
    assert assigned["card_id"] == card["id"]
    assert assigned["card_title"] == "Ship"
    assert assigned["board_name"] == "Roadmap"
    assert assigned["comment_id"] is None
    mention = by_type["comment_mention"]
    assert mention["card_id"] is None
    assert mention["card_title"] == comment.card.title
    assert mention["comment_id"] == comment.id


def test_delete_card_removes_its_assignment_notifications(
    db_session: Any,
    make_user: Callable[..., User],
    make_board: Callable[..., Any],
    make_column: Callable[..., Any],
) -> None:
    admin, member, column = _board_with_members(db_session, make_user, make_board, make_column)
    card = create_card_service(column.id, {"title": "A", "assignee_id": member.id}, admin)
    assert len(_assignment_notifications(db_session)) == 1
    delete_card_service(card["id"], admin)
    assert _assignment_notifications(db_session) == []

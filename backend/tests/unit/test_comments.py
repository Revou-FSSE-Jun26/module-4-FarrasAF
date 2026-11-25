"""Unit tests for the comments service (R5.1-R5.8, R6.1, R6.8, R13, R8.4, R8.6, R8.7)."""

import uuid
from collections.abc import Callable
from typing import Any

import pytest
from sqlalchemy import select

from flask_app.auth.service import create_access_token
from flask_app.comments.schema import CreateCommentSchema
from flask_app.comments.service import (
    create_comment_service,
    delete_comment_service,
    list_comments_service,
    parse_mentions,
    update_comment_service,
)
from flask_app.common.exceptions import (
    AuthorizationError,
    ConflictError,
    ValidationError,
)
from flask_app.common.validation import load_schema
from flask_app.models import ActivityEntry, BoardMembership, Card, Comment, Notification, User


def test_parse_mentions_distinct_and_valid_only() -> None:
    a, b = uuid.uuid4(), uuid.uuid4()
    body = f"hi @[{a}] @[{b}] @[{a}] @[not-a-uuid] @[{'z' * 36}]"
    assert parse_mentions(body) == [a, b]


def test_parse_mentions_empty() -> None:
    assert parse_mentions("no mentions") == []


def test_body_schema_rejects_blank_and_too_long() -> None:
    with pytest.raises(ValidationError):
        load_schema(CreateCommentSchema(), {"body": "   "})
    with pytest.raises(ValidationError):
        load_schema(CreateCommentSchema(), {"body": "x" * 5001})
    assert load_schema(CreateCommentSchema(), {"body": "x" * 5000})["body"] == "x" * 5000


def _member(db_session: Any, card: Card, user: User) -> None:
    db_session.add(BoardMembership(board_id=card.board_id, user_id=user.id, role="member"))
    db_session.flush()


def test_create_comment_notifies_only_distinct_members_and_logs_activity(
    db_session: Any, make_user: Callable[..., User], make_card: Callable[..., Card]
) -> None:
    author, member, outsider = make_user(), make_user(), make_user()
    card = make_card()
    _member(db_session, card, author)
    _member(db_session, card, member)
    body = f"@[{member.id}] @[{member.id}] @[{outsider.id}] @[{uuid.uuid4()}]"
    created = create_comment_service(card.id, {"body": body}, author)
    assert created["version"] == 1 and created["parent_comment_id"] is None
    recipients = db_session.scalars(select(Notification.recipient_id)).all()
    assert recipients == [member.id]
    entry = db_session.scalars(
        select(ActivityEntry).where(ActivityEntry.event_type == "comment_created")
    ).one()
    assert (entry.resource_id, entry.secondary_resource_id) == (created["id"], card.id)


def test_reply_parent_must_be_on_same_card(
    db_session: Any, make_user: Callable[..., User], make_card: Callable[..., Card]
) -> None:
    user = make_user()
    card, other = make_card(), make_card()
    parent = create_comment_service(other.id, {"body": "p"}, user)
    with pytest.raises(ValidationError):
        create_comment_service(card.id, {"body": "r", "parent_comment_id": parent["id"]}, user)
    with pytest.raises(ValidationError):
        create_comment_service(card.id, {"body": "r", "parent_comment_id": uuid.uuid4()}, user)
    ok_parent = create_comment_service(card.id, {"body": "p"}, user)
    reply = create_comment_service(
        card.id, {"body": "r", "parent_comment_id": ok_parent["id"]}, user
    )
    assert reply["parent_comment_id"] == ok_parent["id"]


def test_list_comments_flat_oldest_first(
    db_session: Any, make_user: Callable[..., User], make_card: Callable[..., Card]
) -> None:
    user = make_user()
    card = make_card()
    first = create_comment_service(card.id, {"body": "1"}, user)
    second = create_comment_service(card.id, {"body": "2", "parent_comment_id": first["id"]}, user)
    items = list_comments_service(card.id)["items"]
    assert [c["id"] for c in items] == [first["id"], second["id"]]
    assert items[1]["parent_comment_id"] == first["id"]
    assert items[0]["version"] == 1


def test_update_comment_author_only_and_version(
    db_session: Any, make_user: Callable[..., User], make_card: Callable[..., Card]
) -> None:
    author, other = make_user(), make_user()
    card = make_card()
    comment = create_comment_service(card.id, {"body": "old"}, author)
    with pytest.raises(AuthorizationError):
        update_comment_service(comment["id"], {"body": "x", "version": 1}, other)
    with pytest.raises(ConflictError):
        update_comment_service(comment["id"], {"body": "x"}, author)
    with pytest.raises(ConflictError):
        update_comment_service(comment["id"], {"body": "x", "version": 7}, author)
    updated = update_comment_service(comment["id"], {"body": "new", "version": 1}, author)
    assert updated["body"] == "new" and updated["version"] == 2
    assert updated["edited_at"] is not None
    assert (
        db_session.scalars(
            select(ActivityEntry).where(ActivityEntry.event_type == "comment_edited")
        ).one()
        is not None
    )


def test_delete_comment_cascades_and_author_only(
    db_session: Any, make_user: Callable[..., User], make_card: Callable[..., Card]
) -> None:
    author, other = make_user(), make_user()
    card = make_card()
    parent = create_comment_service(card.id, {"body": "p"}, author)
    create_comment_service(card.id, {"body": "r", "parent_comment_id": parent["id"]}, other)
    with pytest.raises(AuthorizationError):
        delete_comment_service(parent["id"], other)
    delete_comment_service(parent["id"], author)
    db_session.expire_all()
    assert list_comments_service(card.id)["items"] == []
    assert db_session.scalars(select(Comment)).all() == []
    entry = db_session.scalars(
        select(ActivityEntry).where(ActivityEntry.event_type == "comment_deleted")
    ).one()
    assert (entry.resource_id, entry.secondary_resource_id) == (parent["id"], card.id)


# --- Guest rejection (R5.6) ---


def test_guest_non_get_request_returns_403_authorization_error(client: Any) -> None:
    for method in ("post", "patch", "delete"):
        response = getattr(client, method)(f"/api/guest/some-token/cards/{uuid.uuid4()}/comments")
        assert response.status_code == 403
        assert response.get_json()["error"]["code"] == "authorization_error"


def test_user_without_board_role_cannot_write_comment(
    client: Any,
    db_session: Any,
    make_user: Callable[..., User],
    make_card: Callable[..., Card],
) -> None:
    outsider = make_user()
    card = make_card()
    client.set_cookie("access_token", create_access_token(outsider.id))
    response = client.post(f"/api/cards/{card.id}/comments", json={"body": "hello"})
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "authorization_error"
    assert db_session.scalars(select(Comment)).all() == []


def test_request_without_cookies_is_authentication_error(
    client: Any, make_card: Callable[..., Card]
) -> None:
    card = make_card()
    response = client.post(f"/api/cards/{card.id}/comments", json={"body": "hello"})
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "authentication_error"

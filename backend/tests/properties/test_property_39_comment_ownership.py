"""Property 39: Only the author can edit or delete a Comment.

**Validates: Requirements 5.5**
"""

from collections.abc import Callable
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from flask_app.comments.service import (
    create_comment_service,
    delete_comment_service,
    update_comment_service,
)
from flask_app.common.exceptions import AuthorizationError

from flask_app.models import BoardMembership, Card, Comment, User  # isort: skip

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

MakeUser = Callable[..., User]

_BODY = st.text(alphabet="abcdefghij klmnop", min_size=1, max_size=100).filter(
    lambda s: s.strip() != ""
)
_ROLES = st.sampled_from(["admin", "member"])


def _snapshot(comment: Comment) -> tuple[str, int, Any]:
    return (comment.body, comment.version, comment.edited_at)


def _setup(
    db_session: Any,
    make_user: MakeUser,
    make_board: Callable[..., Any],
    make_column: Callable[..., Any],
    make_card: Callable[..., Card],
    role: str,
    body: str,
    reply_count: int,
) -> tuple[User, User, Comment, list[Comment]]:
    author = make_user()
    other = make_user()
    board = make_board(admin=author)
    db_session.add(BoardMembership(board_id=board.id, user_id=other.id, role=role))
    db_session.flush()
    card = make_card(column=make_column(board=board))
    created = create_comment_service(card.id, {"body": body}, author)
    comment = db_session.get(Comment, created["id"])
    replies = []
    for i in range(reply_count):
        reply = create_comment_service(
            card.id, {"body": f"reply {i}", "parent_comment_id": comment.id}, other
        )
        replies.append(db_session.get(Comment, reply["id"]))
    return author, other, comment, replies


# Feature: task-management-app, Property 39: Only the author can edit or delete a Comment
@_SETTINGS
@given(role=_ROLES, body=_BODY, new_body=_BODY, reply_count=st.integers(0, 3))
def test_non_author_cannot_edit_or_delete(
    db_session: Any,
    make_user: MakeUser,
    make_board: Callable[..., Any],
    make_column: Callable[..., Any],
    make_card: Callable[..., Card],
    role: str,
    body: str,
    new_body: str,
    reply_count: int,
) -> None:
    _, other, comment, replies = _setup(
        db_session, make_user, make_board, make_column, make_card, role, body, reply_count
    )
    comment_id = comment.id
    before = _snapshot(comment)
    reply_before = [(r.id, *_snapshot(r)) for r in replies]

    with pytest.raises(AuthorizationError):
        update_comment_service(comment_id, {"body": new_body, "version": comment.version}, other)
    with pytest.raises(AuthorizationError):
        delete_comment_service(comment_id, other)

    db_session.expire_all()
    stored = db_session.get(Comment, comment_id)
    assert stored is not None
    assert _snapshot(stored) == before
    for rid, rbody, rversion, redited in reply_before:
        reply = db_session.get(Comment, rid)
        assert reply is not None
        assert _snapshot(reply) == (rbody, rversion, redited)


# Feature: task-management-app, Property 39: Only the author can edit or delete a Comment
@_SETTINGS
@given(role=_ROLES, body=_BODY, new_body=_BODY, reply_count=st.integers(0, 3))
def test_author_can_edit_and_delete(
    db_session: Any,
    make_user: MakeUser,
    make_board: Callable[..., Any],
    make_column: Callable[..., Any],
    make_card: Callable[..., Card],
    role: str,
    body: str,
    new_body: str,
    reply_count: int,
) -> None:
    author, _, comment, replies = _setup(
        db_session, make_user, make_board, make_column, make_card, role, body, reply_count
    )
    comment_id = comment.id
    version = comment.version

    result = update_comment_service(comment_id, {"body": new_body, "version": version}, author)

    assert result["body"] == new_body
    assert result["version"] == version + 1
    assert result["edited_at"] is not None

    delete_comment_service(comment_id, author)
    db_session.expire_all()
    assert db_session.get(Comment, comment_id) is None

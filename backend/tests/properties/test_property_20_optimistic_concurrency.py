"""Property 20: Optimistic concurrency prevents silent overwrites.

**Validates: Requirements 13.2, 13.3, 13.5, 14.5**
"""

from collections.abc import Callable
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from flask_app.cards.service import update_card_service
from flask_app.comments.service import create_comment_service, update_comment_service
from flask_app.common.exceptions import ConflictError

from flask_app.models import Card, Comment, User  # isort: skip

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

MakeUser = Callable[..., User]

_TEXT = st.text(alphabet="abcdefghij klmnop", min_size=1, max_size=50).filter(
    lambda s: s.strip() != ""
)
_EDITS = st.lists(_TEXT, min_size=1, max_size=4)
_DELTA = st.integers(min_value=-5, max_value=5).filter(lambda d: d != 0)


def _card_state(card: Card) -> tuple[Any, ...]:
    return (card.title, card.version, card.updated_at)


def _comment_state(comment: Comment) -> tuple[Any, ...]:
    return (comment.body, comment.version, comment.edited_at)


def _new_card(
    make_user: MakeUser,
    make_board: Callable[..., Any],
    make_column: Callable[..., Any],
    make_card: Callable[..., Card],
) -> tuple[User, Card]:
    user = make_user()
    board = make_board(admin=user)
    return user, make_card(column=make_column(board=board), title="Original")


def _new_comment(
    db_session: Any,
    make_user: MakeUser,
    make_board: Callable[..., Any],
    make_column: Callable[..., Any],
    make_card: Callable[..., Card],
) -> tuple[User, Comment]:
    user, card = _new_card(make_user, make_board, make_column, make_card)
    created = create_comment_service(card.id, {"body": "Original"}, user)
    return user, db_session.get(Comment, created["id"])


# Feature: task-management-app, Property 20: Optimistic concurrency prevents silent overwrites
@_SETTINGS
@given(new_title=_TEXT, delta=_DELTA)
def test_card_missing_or_mismatched_version_conflicts_and_leaves_card_unchanged(
    db_session: Any,
    make_user: MakeUser,
    make_board: Callable[..., Any],
    make_column: Callable[..., Any],
    make_card: Callable[..., Card],
    new_title: str,
    delta: int,
) -> None:
    user, card = _new_card(make_user, make_board, make_column, make_card)
    card_id = card.id
    before = _card_state(card)

    with pytest.raises(ConflictError):
        update_card_service(card_id, {"title": new_title}, user)
    with pytest.raises(ConflictError):
        update_card_service(card_id, {"title": new_title, "version": before[1] + delta}, user)

    db_session.expire_all()
    assert _card_state(db_session.get(Card, card_id)) == before


# Feature: task-management-app, Property 20: Optimistic concurrency prevents silent overwrites
@_SETTINGS
@given(titles=_EDITS)
def test_card_matching_version_applies_and_version_is_new(
    db_session: Any,
    make_user: MakeUser,
    make_board: Callable[..., Any],
    make_column: Callable[..., Any],
    make_card: Callable[..., Card],
    titles: list[str],
) -> None:
    user, card = _new_card(make_user, make_board, make_column, make_card)
    card_id = card.id
    seen = [card.version]
    for title in titles:
        result = update_card_service(card_id, {"title": title, "version": seen[-1]}, user)
        assert result["title"] == title
        assert result["version"] not in seen
        seen.append(result["version"])

    # A stale version from any earlier edit must now be rejected without effect.
    db_session.expire_all()
    before = _card_state(db_session.get(Card, card_id))
    with pytest.raises(ConflictError):
        update_card_service(card_id, {"title": "stale", "version": seen[0]}, user)
    db_session.expire_all()
    assert _card_state(db_session.get(Card, card_id)) == before


# Feature: task-management-app, Property 20: Optimistic concurrency prevents silent overwrites
@_SETTINGS
@given(new_body=_TEXT, delta=_DELTA)
def test_comment_missing_or_mismatched_version_conflicts_and_leaves_comment_unchanged(
    db_session: Any,
    make_user: MakeUser,
    make_board: Callable[..., Any],
    make_column: Callable[..., Any],
    make_card: Callable[..., Card],
    new_body: str,
    delta: int,
) -> None:
    user, comment = _new_comment(db_session, make_user, make_board, make_column, make_card)
    comment_id = comment.id
    before = _comment_state(comment)

    with pytest.raises(ConflictError):
        update_comment_service(comment_id, {"body": new_body}, user)
    with pytest.raises(ConflictError):
        update_comment_service(comment_id, {"body": new_body, "version": before[1] + delta}, user)

    db_session.expire_all()
    assert _comment_state(db_session.get(Comment, comment_id)) == before


# Feature: task-management-app, Property 20: Optimistic concurrency prevents silent overwrites
@_SETTINGS
@given(bodies=_EDITS)
def test_comment_matching_version_applies_and_version_is_new(
    db_session: Any,
    make_user: MakeUser,
    make_board: Callable[..., Any],
    make_column: Callable[..., Any],
    make_card: Callable[..., Card],
    bodies: list[str],
) -> None:
    user, comment = _new_comment(db_session, make_user, make_board, make_column, make_card)
    comment_id = comment.id
    seen = [comment.version]
    for body in bodies:
        result = update_comment_service(comment_id, {"body": body, "version": seen[-1]}, user)
        assert result["body"] == body
        assert result["version"] not in seen
        seen.append(result["version"])

    db_session.expire_all()
    before = _comment_state(db_session.get(Comment, comment_id))
    with pytest.raises(ConflictError):
        update_comment_service(comment_id, {"body": "stale", "version": seen[0]}, user)
    db_session.expire_all()
    assert _comment_state(db_session.get(Comment, comment_id)) == before

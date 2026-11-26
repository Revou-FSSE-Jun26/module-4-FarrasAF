"""Property 7: Input validation rejects invalid values and leaves state unchanged.

**Validates: Requirements 1.8, 2.6, 3.7, 5.7**
"""

from collections.abc import Callable
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from flask_app.boards.schema import CreateBoardSchema, UpdateBoardSchema
from flask_app.boards.service import create_board_service, update_board_service
from flask_app.cards.schema import CreateCardSchema, UpdateCardSchema
from flask_app.cards.service import create_card_service, update_card_service
from flask_app.columns.schema import CreateColumnSchema, RenameColumnSchema
from flask_app.columns.service import create_column_service, rename_column_service
from flask_app.comments.schema import CreateCommentSchema, UpdateCommentSchema
from flask_app.comments.service import create_comment_service, update_comment_service
from flask_app.common.exceptions import ValidationError
from flask_app.common.validation import load_schema
from tests.conftest import FakeClock

from flask_app.models import (  # isort: skip
    ActivityEntry,
    Board,
    Card,
    Column,
    Comment,
    Notification,
    User,
)

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

_ALPHABET = st.characters(blacklist_categories=["Cs", "Cc", "Z"])
_BLANK = st.text(alphabet=" \t\n", max_size=10)
_PAD = st.text(alphabet=" \t\n", max_size=5)


def _padded_long(min_len: int, max_len: int) -> st.SearchStrategy[str]:
    """Non-whitespace text longer than the limit, with optional padding."""
    core = st.text(alphabet=_ALPHABET, min_size=min_len, max_size=max_len)
    return st.tuples(_PAD, core, _PAD).map("".join)


# Name (Board, Column) and Card title: empty/whitespace-only, or too long after trimming.
invalid_names = st.one_of(_BLANK, _padded_long(101, 150))
invalid_titles = st.one_of(_BLANK, _padded_long(256, 300))
# Comment body: empty, whitespace-only, or over 5000 characters.
invalid_bodies = st.one_of(_BLANK, st.text(alphabet=_ALPHABET, min_size=5001, max_size=5050))

MakeUser = Callable[..., User]


def _state(session: Any) -> dict[str, Any]:
    """Everything the four validated operations could write, as comparable values."""
    session.expire_all()
    return {
        "boards": sorted((b.id, b.name, b.updated_at) for b in session.query(Board)),
        "columns": sorted(
            (c.id, c.name, c.order_index, c.updated_at) for c in session.query(Column)
        ),
        "cards": sorted(
            (c.id, c.title, c.version, c.updated_at, c.order_index) for c in session.query(Card)
        ),
        "comments": sorted((c.id, c.body, c.version, c.updated_at) for c in session.query(Comment)),
        "activity": session.query(ActivityEntry).count(),
        "notifications": session.query(Notification).count(),
    }


def _reject(action: Callable[[], Any], session: Any, before: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        action()
    assert _state(session) == before


# Feature: task-management-app, Property 7: Input validation rejects invalid values and leaves state unchanged  # noqa: E501
@_SETTINGS
@given(name=invalid_names)
def test_invalid_board_name_rejected_and_state_unchanged(
    db_session: Any,
    clock: FakeClock,
    make_user: MakeUser,
    make_team: Callable[..., Any],
    make_board: Callable[..., Any],
    name: str,
) -> None:
    owner = make_user()
    team = make_team(admin=owner)
    board = make_board(team=team, admin=owner, name="Old")
    before = _state(db_session)
    clock.advance(seconds=1)

    _reject(
        lambda: create_board_service(
            load_schema(CreateBoardSchema(), {"team_id": str(team.id), "name": name}), owner
        ),
        db_session,
        before,
    )
    _reject(
        lambda: update_board_service(
            board.id, load_schema(UpdateBoardSchema(), {"name": name}), owner
        ),
        db_session,
        before,
    )


# Feature: task-management-app, Property 7: Input validation rejects invalid values and leaves state unchanged  # noqa: E501
@_SETTINGS
@given(name=invalid_names)
def test_invalid_column_name_rejected_and_state_unchanged(
    db_session: Any,
    clock: FakeClock,
    make_user: MakeUser,
    make_board: Callable[..., Any],
    make_column: Callable[..., Any],
    name: str,
) -> None:
    owner = make_user()
    board = make_board(admin=owner)
    column = make_column(board=board, name="Old")
    before = _state(db_session)
    clock.advance(seconds=1)

    _reject(
        lambda: create_column_service(
            board.id, load_schema(CreateColumnSchema(), {"name": name}), owner
        ),
        db_session,
        before,
    )
    _reject(
        lambda: rename_column_service(column.id, load_schema(RenameColumnSchema(), {"name": name})),
        db_session,
        before,
    )


# Feature: task-management-app, Property 7: Input validation rejects invalid values and leaves state unchanged  # noqa: E501
@_SETTINGS
@given(title=invalid_titles)
def test_invalid_card_title_rejected_and_state_unchanged(
    db_session: Any,
    clock: FakeClock,
    make_user: MakeUser,
    make_board: Callable[..., Any],
    make_column: Callable[..., Any],
    make_card: Callable[..., Any],
    title: str,
) -> None:
    owner = make_user()
    column = make_column(board=make_board(admin=owner))
    card = make_card(column=column, title="Old")
    before = _state(db_session)
    clock.advance(seconds=1)

    _reject(
        lambda: create_card_service(
            column.id, load_schema(CreateCardSchema(), {"title": title}), owner
        ),
        db_session,
        before,
    )
    _reject(
        lambda: update_card_service(
            card.id,
            load_schema(UpdateCardSchema(), {"title": title, "version": card.version}),
            owner,
        ),
        db_session,
        before,
    )


# Feature: task-management-app, Property 7: Input validation rejects invalid values and leaves state unchanged  # noqa: E501
@_SETTINGS
@given(body=invalid_bodies)
def test_invalid_comment_body_rejected_and_state_unchanged(
    db_session: Any,
    clock: FakeClock,
    make_user: MakeUser,
    make_board: Callable[..., Any],
    make_column: Callable[..., Any],
    make_card: Callable[..., Any],
    body: str,
) -> None:
    owner = make_user()
    card = make_card(column=make_column(board=make_board(admin=owner)))
    comment = create_comment_service(card.id, {"body": "Old"}, owner)
    before = _state(db_session)
    clock.advance(seconds=1)

    _reject(
        lambda: create_comment_service(
            card.id, load_schema(CreateCommentSchema(), {"body": body}), owner
        ),
        db_session,
        before,
    )
    _reject(
        lambda: update_comment_service(
            comment["id"],
            load_schema(UpdateCommentSchema(), {"body": body, "version": comment["version"]}),
            owner,
        ),
        db_session,
        before,
    )

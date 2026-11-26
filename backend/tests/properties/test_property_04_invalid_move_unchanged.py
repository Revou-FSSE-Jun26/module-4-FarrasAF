"""Property 4: Out-of-range or cross-board moves leave position unchanged.

**Validates: Requirements 2.7, 4.4, 4.5**
"""

from collections.abc import Callable
from datetime import datetime
from typing import Any
from uuid import UUID

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import select

from flask_app.cards.service import create_card_service, move_card_service
from flask_app.columns.service import reorder_column_service
from flask_app.common.exceptions import ValidationError
from flask_app.models import Board, Card, Column, User

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

MakeUser = Callable[..., User]
MakeBoard = Callable[..., Board]
MakeColumn = Callable[..., Column]

CardState = dict[UUID, tuple[UUID, int, datetime]]

_NON_INTEGERS = st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(max_size=5),
    st.none(),
    st.booleans(),
)


def _card_state(db_session: Any) -> CardState:
    db_session.expire_all()
    cards = db_session.execute(select(Card)).scalars().all()
    return {card.id: (card.column_id, card.order_index, card.updated_at) for card in cards}


def _column_state(db_session: Any, board_id: UUID) -> list[tuple[UUID, int]]:
    db_session.expire_all()
    rows = db_session.execute(
        select(Column.id, Column.order_index).where(Column.board_id == board_id)
    ).all()
    return sorted((row[0], row[1]) for row in rows)


def _populate(actor: User, column_ids: list[UUID], sizes: list[int]) -> list[UUID]:
    card_ids: list[UUID] = []
    for column_id, size in zip(column_ids, sizes, strict=False):
        for _ in range(size):
            card_ids.append(create_card_service(column_id, {"title": "Task"}, actor)["id"])
    return card_ids


# Feature: task-management-app, Property 4: Out-of-range or cross-board moves leave position unchanged  # noqa: E501
@_SETTINGS
@given(
    sizes=st.lists(st.integers(0, 4), min_size=2, max_size=2),
    card_selector=st.integers(0, 1000),
    column_selector=st.integers(0, 1000),
    kind=st.sampled_from(["negative", "too_large", "non_integer"]),
    magnitude=st.integers(1, 50),
    non_integer=_NON_INTEGERS,
)
def test_invalid_card_move_is_rejected_and_state_unchanged(
    db_session: Any,
    make_user: MakeUser,
    make_board: MakeBoard,
    make_column: MakeColumn,
    sizes: list[int],
    card_selector: int,
    column_selector: int,
    kind: str,
    magnitude: int,
    non_integer: Any,
) -> None:
    actor = make_user()
    board = make_board(admin=actor)
    columns = [make_column(board=board) for _ in range(2)]
    column_ids = [column.id for column in columns]
    card_ids = _populate(actor, column_ids, [max(sizes[0], 1), sizes[1]])

    card_id = card_ids[card_selector % len(card_ids)]
    source_id = db_session.get(Card, card_id).column_id
    target_id = column_ids[column_selector % 2]
    target_size = db_session.query(Card).filter(Card.column_id == target_id).count()
    remaining = target_size - (1 if target_id == source_id else 0)

    target_index: Any
    if kind == "negative":
        target_index = -magnitude
    elif kind == "too_large":
        target_index = remaining + magnitude
    else:
        target_index = non_integer

    before = _card_state(db_session)
    with pytest.raises(ValidationError):
        move_card_service(card_id, target_id, target_index, actor)
    assert _card_state(db_session) == before


# Feature: task-management-app, Property 4: Out-of-range or cross-board moves leave position unchanged  # noqa: E501
@_SETTINGS
@given(
    sizes=st.lists(st.integers(0, 3), min_size=2, max_size=2),
    card_selector=st.integers(0, 1000),
    index_selector=st.integers(0, 1000),
)
def test_cross_board_card_move_is_rejected_and_state_unchanged(
    db_session: Any,
    make_user: MakeUser,
    make_board: MakeBoard,
    make_column: MakeColumn,
    sizes: list[int],
    card_selector: int,
    index_selector: int,
) -> None:
    actor = make_user()
    board = make_board(admin=actor)
    other_board = make_board(admin=actor)
    own_column = make_column(board=board)
    foreign_column = make_column(board=other_board)
    card_ids = _populate(actor, [own_column.id, foreign_column.id], [max(sizes[0], 1), sizes[1]])

    card_id = card_ids[card_selector % len(card_ids)]
    if db_session.get(Card, card_id).board_id != board.id:
        card_id = card_ids[0]
    # Any index, including one that would be valid in the foreign column.
    target_index = index_selector % (sizes[1] + 2)

    before = _card_state(db_session)
    with pytest.raises(ValidationError):
        move_card_service(card_id, foreign_column.id, target_index, actor)
    assert _card_state(db_session) == before


# Feature: task-management-app, Property 4: Out-of-range or cross-board moves leave position unchanged  # noqa: E501
@_SETTINGS
@given(
    column_count=st.integers(1, 5),
    column_selector=st.integers(0, 1000),
    kind=st.sampled_from(["negative", "too_large"]),
    magnitude=st.integers(1, 50),
)
def test_invalid_column_reorder_is_rejected_and_order_unchanged(
    db_session: Any,
    make_board: MakeBoard,
    make_column: MakeColumn,
    column_count: int,
    column_selector: int,
    kind: str,
    magnitude: int,
) -> None:
    board = make_board()
    columns = [make_column(board=board) for _ in range(column_count)]
    column = columns[column_selector % column_count]
    target_index = -magnitude if kind == "negative" else column_count - 1 + magnitude

    before = _column_state(db_session, board.id)
    with pytest.raises(ValidationError):
        reorder_column_service(column.id, {"target_index": target_index})
    assert _column_state(db_session, board.id) == before

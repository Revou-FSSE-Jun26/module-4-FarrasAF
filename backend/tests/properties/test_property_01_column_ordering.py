"""Property 1: Column ordering is always contiguous from zero.

**Validates: Requirements 2.1, 2.3, 2.5**
"""

from collections.abc import Callable
from typing import Any
from uuid import UUID

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import select

from flask_app.columns.service import (
    create_column_service,
    delete_column_service,
    reorder_column_service,
)
from flask_app.models import Board, Column, User

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

MakeUser = Callable[..., User]
MakeBoard = Callable[..., Board]
MakeColumn = Callable[..., Column]

# Each operation is (kind, selector); the selector is reduced modulo the
# current Column count to pick a Column or a target index.
operations = st.lists(
    st.tuples(st.sampled_from(["create", "reorder", "delete"]), st.integers(0, 1000)),
    min_size=1,
    max_size=15,
)


def _order_indexes(db_session: Any, board_id: UUID) -> list[int]:
    db_session.expire_all()
    query = (
        select(Column.order_index).where(Column.board_id == board_id).order_by(Column.order_index)
    )
    return list(db_session.scalars(query))


def _column_ids(db_session: Any, board_id: UUID) -> list[UUID]:
    query = select(Column.id).where(Column.board_id == board_id).order_by(Column.order_index)
    return list(db_session.scalars(query))


# Feature: task-management-app, Property 1: Column ordering is always contiguous from zero
@_SETTINGS
@given(initial=st.integers(0, 3), ops=operations)
def test_column_order_indexes_stay_contiguous_from_zero(
    db_session: Any,
    make_user: MakeUser,
    make_board: MakeBoard,
    make_column: MakeColumn,
    initial: int,
    ops: list[tuple[str, int]],
) -> None:
    admin = make_user()
    board = make_board(admin=admin)
    board_id = board.id
    for _ in range(initial):
        make_column(board=board)
    assert _order_indexes(db_session, board_id) == list(range(initial))

    for kind, selector in ops:
        before = _order_indexes(db_session, board_id)
        count = len(before)
        if kind == "create":
            created = create_column_service(board_id, {"name": "New"}, admin)
            assert created["order_index"] == count
        elif count == 0:
            continue
        elif kind == "reorder":
            column_id = _column_ids(db_session, board_id)[selector % count]
            reorder_column_service(column_id, {"target_index": (selector // 7) % count})
        else:
            column_id = _column_ids(db_session, board_id)[selector % count]
            delete_column_service(column_id, admin)

        after = _order_indexes(db_session, board_id)
        expected = count + 1 if kind == "create" else count - 1 if kind == "delete" else count
        assert after == list(range(expected))

"""Property 9: A Column containing Cards cannot be deleted.

**Validates: Requirements 2.4**
"""

from collections.abc import Callable
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import select

from flask_app.columns.service import delete_column_service
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
MakeCard = Callable[..., Card]


# Feature: task-management-app, Property 9: Non-empty column cannot be deleted
@_SETTINGS
@given(
    column_count=st.integers(1, 4),
    card_count=st.integers(1, 6),
    selector=st.integers(0, 1000),
)
def test_non_empty_column_cannot_be_deleted(
    db_session: Any,
    make_user: MakeUser,
    make_board: MakeBoard,
    make_column: MakeColumn,
    make_card: MakeCard,
    column_count: int,
    card_count: int,
    selector: int,
) -> None:
    admin = make_user()
    board = make_board(admin=admin)
    board_id = board.id
    columns = [make_column(board=board) for _ in range(column_count)]
    target = columns[selector % column_count]
    target_id = target.id
    for _ in range(card_count):
        make_card(column=target, created_by=admin)

    def _snapshot() -> tuple[list[tuple[Any, int]], list[tuple[Any, int]]]:
        db_session.expire_all()
        cols = db_session.execute(
            select(Column.id, Column.order_index)
            .where(Column.board_id == board_id)
            .order_by(Column.order_index)
        ).all()
        cards = db_session.execute(
            select(Card.id, Card.order_index)
            .where(Card.column_id == target_id)
            .order_by(Card.order_index)
        ).all()
        return [tuple(r) for r in cols], [tuple(r) for r in cards]

    before = _snapshot()

    with pytest.raises(ValidationError):
        delete_column_service(target_id, admin)

    after = _snapshot()
    assert after == before
    assert len(after[1]) == card_count

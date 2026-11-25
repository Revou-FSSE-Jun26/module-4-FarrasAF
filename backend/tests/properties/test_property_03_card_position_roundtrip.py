"""Property 3: Card position round-trip persistence.

**Validates: Requirements 4.3**
"""

from collections.abc import Callable
from typing import Any

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import select

from flask_app.cards.service import create_card_service, move_card_service
from flask_app.models import Board, Card, Column, User

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

MakeUser = Callable[..., User]
MakeBoard = Callable[..., Board]
MakeColumn = Callable[..., Column]


# Feature: task-management-app, Property 3: Card position round-trip persistence
@_SETTINGS
@given(
    column_count=st.integers(1, 3),
    sizes=st.lists(st.integers(0, 5), min_size=3, max_size=3),
    card_selector=st.integers(0, 1000),
    column_selector=st.integers(0, 1000),
    index_selector=st.integers(0, 1000),
)
def test_moved_card_position_persists_after_reload(
    db_session: Any,
    make_user: MakeUser,
    make_board: MakeBoard,
    make_column: MakeColumn,
    column_count: int,
    sizes: list[int],
    card_selector: int,
    column_selector: int,
    index_selector: int,
) -> None:
    actor = make_user()
    board = make_board(admin=actor)
    columns = [make_column(board=board) for _ in range(column_count)]
    column_ids = [column.id for column in columns]

    created: list[tuple[Any, Any]] = []
    for column_id, size in zip(column_ids, sizes, strict=False):
        for _ in range(size):
            card = create_card_service(column_id, {"title": "Task"}, actor)
            created.append((card["id"], column_id))
    if not created:
        card = create_card_service(column_ids[0], {"title": "Task"}, actor)
        created.append((card["id"], column_ids[0]))

    card_id, source_id = created[card_selector % len(created)]
    target_id = column_ids[column_selector % column_count]
    target_size = db_session.query(Card).filter(Card.column_id == target_id).count()
    remaining = target_size - (1 if target_id == source_id else 0)
    target_index = index_selector % (remaining + 1)

    move_card_service(card_id, target_id, target_index, actor)

    db_session.expire_all()
    reloaded = db_session.execute(select(Card).where(Card.id == card_id)).scalar_one()
    assert reloaded.column_id == target_id
    assert reloaded.order_index == target_index

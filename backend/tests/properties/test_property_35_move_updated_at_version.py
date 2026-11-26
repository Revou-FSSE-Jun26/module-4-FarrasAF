"""Property 35: Card move changes only the moved Card's updated_at and never its version.

**Validates: Requirements 4.7, 13.6**
"""

from collections.abc import Callable
from datetime import datetime
from typing import Any
from uuid import UUID

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from flask_app.cards.service import create_card_service, move_card_service
from flask_app.models import Board, Card, Column, User
from tests.conftest import FakeClock

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

MakeUser = Callable[..., User]
MakeBoard = Callable[..., Board]
MakeColumn = Callable[..., Column]


def _snapshot(db_session: Any, card_ids: list[UUID]) -> dict[UUID, tuple[int, datetime]]:
    db_session.expire_all()
    cards = [db_session.get(Card, card_id) for card_id in card_ids]
    return {card.id: (card.version, card.updated_at) for card in cards}


# Feature: task-management-app, Property 35: Card move changes only the moved Card's updated_at and never its version  # noqa: E501
@_SETTINGS
@given(
    sizes=st.lists(st.integers(0, 4), min_size=2, max_size=3),
    card_selector=st.integers(0, 1000),
    column_selector=st.integers(0, 1000),
    index_selector=st.integers(0, 1000),
    delay_seconds=st.integers(1, 100_000),
)
def test_move_changes_only_moved_card_updated_at_and_never_version(
    db_session: Any,
    clock: FakeClock,
    make_user: MakeUser,
    make_board: MakeBoard,
    make_column: MakeColumn,
    sizes: list[int],
    card_selector: int,
    column_selector: int,
    index_selector: int,
    delay_seconds: int,
) -> None:
    actor = make_user()
    board = make_board(admin=actor)
    columns = [make_column(board=board) for _ in sizes]
    card_ids: list[UUID] = []
    for column, size in zip(columns, [max(sizes[0], 1), *sizes[1:]], strict=True):
        for _ in range(size):
            card_ids.append(create_card_service(column.id, {"title": "Task"}, actor)["id"])

    moved_id = card_ids[card_selector % len(card_ids)]
    source_id = db_session.get(Card, moved_id).column_id
    target = columns[column_selector % len(columns)]
    target_size = db_session.query(Card).filter(Card.column_id == target.id).count()
    remaining = target_size - (1 if target.id == source_id else 0)
    target_index = index_selector % (remaining + 1)

    before = _snapshot(db_session, card_ids)
    moved_at = clock.advance(seconds=delay_seconds)

    result = move_card_service(moved_id, target.id, target_index, actor)

    after = _snapshot(db_session, card_ids)
    assert result["version"] == before[moved_id][0]
    assert result["updated_at"] == moved_at
    for card_id in card_ids:
        assert after[card_id][0] == before[card_id][0]
        if card_id == moved_id:
            assert after[card_id][1] == moved_at
        else:
            assert after[card_id][1] == before[card_id][1]

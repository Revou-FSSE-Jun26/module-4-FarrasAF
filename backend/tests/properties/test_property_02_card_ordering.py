"""Property 2: Card ordering is always contiguous from zero.

**Validates: Requirements 3.2, 3.5, 4.1, 4.2**
"""

from collections.abc import Callable
from typing import Any
from uuid import UUID

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import select

from flask_app.cards.service import (
    create_card_service,
    delete_card_service,
    move_card_service,
)
from flask_app.models import Board, Card, Column, User

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

MakeUser = Callable[..., User]
MakeBoard = Callable[..., Board]
MakeColumn = Callable[..., Column]

# Each operation is (kind, a, b, c); selectors are reduced modulo the current
# sizes to pick a Column, a Card, or a target index.
operations = st.lists(
    st.tuples(
        st.sampled_from(["create", "move", "delete"]),
        st.integers(0, 1000),
        st.integers(0, 1000),
        st.integers(0, 1000),
    ),
    min_size=1,
    max_size=15,
)


def _layout(db_session: Any, column_ids: list[UUID]) -> dict[UUID, list[tuple[UUID, int]]]:
    """Return (card id, order_index) pairs per Column, ordered by order_index."""
    db_session.expire_all()
    result: dict[UUID, list[tuple[UUID, int]]] = {}
    for column_id in column_ids:
        rows = db_session.execute(
            select(Card.id, Card.order_index)
            .where(Card.column_id == column_id)
            .order_by(Card.order_index)
        ).all()
        result[column_id] = [(row[0], row[1]) for row in rows]
    return result


def _assert_contiguous(layout: dict[UUID, list[tuple[UUID, int]]]) -> None:
    for entries in layout.values():
        assert [index for _, index in entries] == list(range(len(entries)))


# Feature: task-management-app, Property 2: Card ordering is always contiguous from zero
@_SETTINGS
@given(
    column_count=st.integers(1, 3),
    initial=st.lists(st.integers(0, 4), min_size=3, max_size=3),
    ops=operations,
)
def test_card_order_indexes_stay_contiguous_from_zero(
    db_session: Any,
    make_user: MakeUser,
    make_board: MakeBoard,
    make_column: MakeColumn,
    column_count: int,
    initial: list[int],
    ops: list[tuple[str, int, int, int]],
) -> None:
    actor = make_user()
    board = make_board(admin=actor)
    columns = [make_column(board=board) for _ in range(column_count)]
    column_ids = [column.id for column in columns]

    for column_id, size in zip(column_ids, initial, strict=False):
        for _ in range(size):
            create_card_service(column_id, {"title": "Task"}, actor)
    layout = _layout(db_session, column_ids)
    _assert_contiguous(layout)

    for kind, a, b, c in ops:
        before = _layout(db_session, column_ids)
        sizes = {cid: len(entries) for cid, entries in before.items()}
        all_cards = [(cid, card_id) for cid, entries in before.items() for card_id, _ in entries]
        expected = dict(sizes)

        if kind == "create":
            target = column_ids[a % column_count]
            created = create_card_service(target, {"title": "New"}, actor)
            assert created["order_index"] == sizes[target]
            expected[target] += 1
        elif not all_cards:
            continue
        elif kind == "move":
            source, card_id = all_cards[a % len(all_cards)]
            target = column_ids[b % column_count]
            remaining = sizes[target] - (1 if target == source else 0)
            index = c % (remaining + 1)
            moved = move_card_service(card_id, target, index, actor)
            assert moved["order_index"] == index
            if target != source:
                expected[source] -= 1
                expected[target] += 1
        else:
            source, card_id = all_cards[a % len(all_cards)]
            delete_card_service(card_id, actor)
            expected[source] -= 1

        after = _layout(db_session, column_ids)
        _assert_contiguous(after)
        assert {cid: len(entries) for cid, entries in after.items()} == expected

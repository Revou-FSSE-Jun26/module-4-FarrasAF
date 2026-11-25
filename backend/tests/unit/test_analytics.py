"""Unit tests for the analytics module (R9.1-R9.6)."""

import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest

from flask_app.analytics.service import compute_completion_rate, get_analytics_service
from flask_app.models import ActivityEntry, Board, Card, Column, User


@pytest.mark.parametrize(
    ("counts", "expected"),
    [
        ([], 0.0),
        ([("To Do", 0), ("Done", 0)], 0.0),
        ([("To Do", 3)], 0.0),
        ([("To Do", 1), ("Done", 1)], 0.5),
        ([("Done", 1), ("Done", 1), ("Doing", 2)], 0.5),
        ([("done", 2), ("Done ", 2)], 0.0),
    ],
)
def test_compute_completion_rate(counts: list[tuple[str, int]], expected: float) -> None:
    assert compute_completion_rate(counts) == expected


def test_empty_board(make_user: Callable[..., User], make_board: Callable[..., Board]) -> None:
    board = make_board(admin=make_user())
    result = get_analytics_service(board.id)
    assert result["total_cards"] == 0
    assert result["completion_rate"] == 0.0
    assert result["activity_by_day"] == []


def test_counts_rate_and_utc_days(
    db_session: Any,
    make_user: Callable[..., User],
    make_board: Callable[..., Board],
    make_column: Callable[..., Column],
    make_card: Callable[..., Card],
) -> None:
    user = make_user()
    board = make_board(admin=user)
    todo = make_column(board=board, name="To Do")
    done = make_column(board=board, name="Done")
    make_card(column=todo, title="a")
    make_card(column=done, title="b")
    make_card(column=done, title="c")
    for ts in (
        datetime(2024, 1, 1, 23, 30, tzinfo=UTC),
        datetime(2024, 1, 2, 0, 15, tzinfo=UTC),
        datetime(2024, 1, 2, 5, 0, tzinfo=UTC),
    ):
        db_session.add(
            ActivityEntry(
                board_id=board.id,
                actor_id=user.id,
                event_type="card_created",
                resource_id=uuid.uuid4(),
                created_at=ts,
            )
        )
    db_session.flush()

    result = get_analytics_service(board.id)
    counts = {c["column_id"]: c["count"] for c in result["per_column"]}
    assert counts[todo.id] == 1
    assert counts[done.id] == 2
    assert result["total_cards"] == 3
    assert result["completion_rate"] == pytest.approx(2 / 3)
    assert result["activity_by_day"] == [
        {"day": "2024-01-01", "count": 1},
        {"day": "2024-01-02", "count": 2},
    ]

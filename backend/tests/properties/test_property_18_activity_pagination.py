"""Property 18: Activity pagination visits each entry exactly once in order.

**Validates: Requirements 8.12, 8.15**
"""

import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from flask_app.activity.service import list_activity_service
from flask_app.common.pagination import ACTIVITY_PAGE_SIZE
from flask_app.models import ActivityEntry, Board, User

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)

_BASE_TIME = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)

# Few distinct timestamps force many equal created_at values, so the id tie-break
# is exercised. Sizes cross zero, one, exact-multiple and partial last pages.
_OFFSETS = st.one_of(
    st.lists(st.integers(0, 4), max_size=2 * ACTIVITY_PAGE_SIZE + 50),
    st.sampled_from(
        [0, 1, ACTIVITY_PAGE_SIZE - 1, ACTIVITY_PAGE_SIZE, ACTIVITY_PAGE_SIZE + 1]
    ).flatmap(lambda n: st.lists(st.integers(0, 4), min_size=n, max_size=n)),
)


# Feature: task-management-app, Property 18: Activity pagination visits each entry exactly once in order  # noqa: E501
@_SETTINGS
@given(offsets=_OFFSETS, beyond=st.integers(0, 5), negative=st.integers(-(10**6), -1))
def test_activity_pagination_visits_each_entry_once_in_order(
    db_session: Any,
    make_user: Callable[..., User],
    make_board: Callable[..., Board],
    offsets: list[int],
    beyond: int,
    negative: int,
) -> None:
    # A fresh Board per example isolates entries; other Boards' entries must never leak in.
    actor = make_user()
    board = make_board(admin=actor)
    other_board = make_board(admin=actor)
    entries = [
        ActivityEntry(
            id=uuid.uuid4(),
            board_id=board.id,
            actor_id=actor.id,
            event_type="card_created",
            resource_id=uuid.uuid4(),
            created_at=_BASE_TIME + timedelta(seconds=offset),
        )
        for offset in offsets
    ]
    db_session.add_all(entries)
    db_session.add(
        ActivityEntry(
            board_id=other_board.id,
            actor_id=actor.id,
            event_type="card_created",
            resource_id=uuid.uuid4(),
        )
    )
    db_session.flush()

    expected = [e.id for e in sorted(entries, key=lambda e: (e.created_at, e.id), reverse=True)]
    last_page = max(0, -(-len(expected) // ACTIVITY_PAGE_SIZE) - 1)

    visited: list[uuid.UUID] = []
    for page in range(last_page + 1):
        items = list_activity_service(board.id, {"page": page})["items"]
        assert len(items) <= ACTIVITY_PAGE_SIZE
        visited.extend(item["id"] for item in items)

    assert visited == expected
    assert len(set(visited)) == len(visited)

    first_missing = last_page + 1 + beyond
    assert list_activity_service(board.id, {"page": first_missing})["items"] == []
    assert list_activity_service(board.id, {"page": negative})["items"] == []

"""Unit tests for the activity module (R8.1, R8.12-R8.15)."""

import uuid
from collections.abc import Callable
from typing import Any

import pytest

from flask_app.activity.schema import ActivityQuerySchema
from flask_app.activity.service import list_activity_service, record_activity
from flask_app.common.exceptions import ValidationError
from flask_app.common.pagination import ACTIVITY_PAGE_SIZE
from flask_app.common.validation import load_schema
from flask_app.models import Board, User
from flask_app.models.activity_entry import EVENT_TYPES
from tests.conftest import FakeClock


def test_record_activity_accepts_all_event_types_without_committing(
    db_session: Any, make_user: Callable[..., User], make_board: Callable[..., Board]
) -> None:
    actor = make_user()
    board = make_board(admin=actor)
    for event_type in EVENT_TYPES:
        record_activity(board.id, actor.id, event_type, uuid.uuid4())
    db_session.flush()
    result = list_activity_service(board.id, {})
    assert {item["event_type"] for item in result["items"]} == set(EVENT_TYPES)


def test_record_activity_rejects_unknown_event_type(
    make_user: Callable[..., User], make_board: Callable[..., Board]
) -> None:
    actor = make_user()
    board = make_board(admin=actor)
    with pytest.raises(ValueError):
        record_activity(board.id, actor.id, "card_exploded", uuid.uuid4())


def test_list_activity_item_fields_and_secondary_resource(
    db_session: Any, make_user: Callable[..., User], make_board: Callable[..., Board]
) -> None:
    actor = make_user(display_name="Ada")
    board = make_board(admin=actor)
    resource, secondary = uuid.uuid4(), uuid.uuid4()
    record_activity(board.id, actor.id, "card_moved", resource, secondary)
    db_session.flush()
    (item,) = list_activity_service(board.id, {"page": 0})["items"]
    assert item["event_type"] == "card_moved"
    assert item["actor"] == {"id": actor.id, "display_name": "Ada"}
    assert item["resource_id"] == resource
    assert item["secondary_resource_id"] == secondary
    assert item["created_at"] is not None


def test_list_activity_orders_newest_first_and_pages(
    db_session: Any,
    clock: FakeClock,
    make_user: Callable[..., User],
    make_board: Callable[..., Board],
) -> None:
    actor = make_user()
    board = make_board(admin=actor)
    other_board = make_board()
    total = ACTIVITY_PAGE_SIZE + 5
    ids = []
    for _ in range(total):
        clock.advance(seconds=1)
        entry = record_activity(board.id, actor.id, "card_created", uuid.uuid4())
        db_session.flush()  # created_at default is applied at flush time
        ids.append(entry.id)
    record_activity(other_board.id, actor.id, "card_created", uuid.uuid4())
    db_session.flush()

    first = list_activity_service(board.id, {"page": 0})
    second = list_activity_service(board.id, {"page": 1})
    assert first["page_size"] == ACTIVITY_PAGE_SIZE
    assert [i["id"] for i in first["items"]] == ids[::-1][:ACTIVITY_PAGE_SIZE]
    assert [i["id"] for i in second["items"]] == ids[::-1][ACTIVITY_PAGE_SIZE:]


@pytest.mark.parametrize("page", [-1, 2, 10**15])
def test_list_activity_out_of_range_page_is_empty(
    db_session: Any, make_user: Callable[..., User], make_board: Callable[..., Board], page: int
) -> None:
    actor = make_user()
    board = make_board(admin=actor)
    record_activity(board.id, actor.id, "card_created", uuid.uuid4())
    db_session.flush()
    result = list_activity_service(board.id, {"page": page})
    assert result["items"] == []
    assert result["page"] == page


def test_query_schema_page_is_strict_integer() -> None:
    assert load_schema(ActivityQuerySchema(), {"page": "3"}) == {"page": 3}
    assert load_schema(ActivityQuerySchema(), {"page": "-1"}) == {"page": -1}
    assert load_schema(ActivityQuerySchema(), {}) == {}
    for bad in ("1.5", "abc", "", " 1", "1e2"):
        with pytest.raises(ValidationError):
            load_schema(ActivityQuerySchema(), {"page": bad})
    with pytest.raises(ValidationError):
        load_schema(ActivityQuerySchema(), {"page": "0", "extra": "x"})

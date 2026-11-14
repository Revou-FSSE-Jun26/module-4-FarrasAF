"""Property 15: Notification cursor codec round-trip.

**Validates: Requirements 6.10**
"""

import re
import uuid
from datetime import UTC, datetime, timedelta, timezone

from hypothesis import given, settings
from hypothesis import strategies as st

from flask_app.common.cursor import decode_cursor, encode_cursor
from flask_app.common.exceptions import ValidationError

utc_datetimes = st.datetimes(timezones=st.just(UTC))
offset_datetimes = st.datetimes(
    min_value=datetime(2, 1, 1),
    max_value=datetime(9998, 1, 1),
    timezones=st.integers(min_value=-14 * 60, max_value=14 * 60).map(
        lambda m: timezone(timedelta(minutes=m))
    ),
)
uuids = st.uuids()


# Feature: task-management-app, Property 15: Notification cursor codec round-trip
@settings(max_examples=200)
@given(created_at=utc_datetimes, item_id=uuids)
def test_cursor_round_trip(created_at: datetime, item_id: uuid.UUID) -> None:
    token = encode_cursor(created_at, item_id)

    assert decode_cursor(token) == (created_at, item_id)
    assert re.fullmatch(r"[A-Za-z0-9_-]+", token)


# Feature: task-management-app, Property 15: Notification cursor codec round-trip
@settings(max_examples=200)
@given(created_at=offset_datetimes, item_id=uuids)
def test_cursor_round_trip_preserves_instant_for_offsets(
    created_at: datetime, item_id: uuid.UUID
) -> None:
    decoded_at, decoded_id = decode_cursor(encode_cursor(created_at, item_id))

    assert decoded_at == created_at
    assert decoded_at.utcoffset() == timedelta(0)
    assert decoded_id == item_id


# Feature: task-management-app, Property 15: Notification cursor codec round-trip
@settings(max_examples=200)
@given(token=st.one_of(st.text(), st.from_regex(r"[A-Za-z0-9_-]{0,120}", fullmatch=True)))
def test_arbitrary_strings_decode_or_raise_validation_error(token: str) -> None:
    try:
        created_at, item_id = decode_cursor(token)
    except ValidationError as exc:
        assert exc.field == "cursor"
    else:
        assert created_at.utcoffset() == timedelta(0)
        assert isinstance(item_id, uuid.UUID)

"""Property 5: Board partial update preserves omitted fields; invalid field rejects atomically.

**Validates: Requirements 1.3, 1.10**
"""

from collections.abc import Callable
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from flask_app.boards.schema import UpdateBoardSchema
from flask_app.boards.service import update_board_service
from flask_app.common.exceptions import ValidationError
from flask_app.common.validation import load_schema
from flask_app.models import Board, User

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

_ALPHABET = st.characters(blacklist_categories=["Cs", "Cc", "Zs"])
_PAD = st.text(alphabet=" \t\n", max_size=5)
_NAME_CORE = st.text(alphabet=_ALPHABET, min_size=1, max_size=100)
valid_names = st.tuples(_PAD, _NAME_CORE, _PAD).map("".join)
valid_descriptions = st.text(alphabet=_ALPHABET, max_size=2000)
valid_visibilities = st.sampled_from(["private", "team"])

invalid_names = st.one_of(
    _PAD.map(lambda pad: pad),  # empty or whitespace only
    st.text(alphabet=_ALPHABET, min_size=101, max_size=150),
)
invalid_descriptions = st.text(alphabet=_ALPHABET, min_size=2001, max_size=2100)
invalid_visibilities = st.text(max_size=10).filter(lambda s: s not in ("private", "team"))

_VALID = {
    "name": valid_names,
    "description": valid_descriptions,
    "visibility": valid_visibilities,
}
_INVALID = {
    "name": invalid_names,
    "description": invalid_descriptions,
    "visibility": invalid_visibilities,
}

valid_payloads = st.fixed_dictionaries({}, optional=_VALID)

MakeUser = Callable[..., User]
MakeBoard = Callable[..., Board]


@st.composite
def invalid_payloads(draw: st.DrawFn) -> dict[str, Any]:
    payload: dict[str, Any] = draw(valid_payloads)
    bad_field = draw(st.sampled_from(sorted(_INVALID)))
    payload[bad_field] = draw(_INVALID[bad_field])
    return payload


def _snapshot(board: Board) -> dict[str, Any]:
    return {
        "name": board.name,
        "description": board.description,
        "visibility": board.visibility,
    }


# Feature: task-management-app, Property 5: Board partial update preserves omitted fields; invalid field rejects atomically  # noqa: E501
@_SETTINGS
@given(payload=valid_payloads)
def test_supplied_fields_persist_and_omitted_fields_unchanged(
    db_session: Any, make_user: MakeUser, make_board: MakeBoard, payload: dict[str, Any]
) -> None:
    admin = make_user()
    board = make_board(admin=admin, name="Original", description="Old text", visibility="private")
    before = _snapshot(board)

    result = update_board_service(board.id, load_schema(UpdateBoardSchema(), payload), admin)

    expected = dict(before)
    for field, value in payload.items():
        expected[field] = value.strip() if field == "name" else value
    for field, value in expected.items():
        assert result[field] == value
    db_session.expire_all()
    assert _snapshot(db_session.get(Board, board.id)) == expected


# Feature: task-management-app, Property 5: Board partial update preserves omitted fields; invalid field rejects atomically  # noqa: E501
@_SETTINGS
@given(payload=invalid_payloads())
def test_any_invalid_field_rejects_and_leaves_all_fields_unchanged(
    db_session: Any, make_user: MakeUser, make_board: MakeBoard, payload: dict[str, Any]
) -> None:
    admin = make_user()
    board = make_board(admin=admin, name="Original", description="Old text", visibility="team")
    before = _snapshot(board)

    with pytest.raises(ValidationError):
        update_board_service(board.id, load_schema(UpdateBoardSchema(), payload), admin)

    db_session.expire_all()
    assert _snapshot(db_session.get(Board, board.id)) == before

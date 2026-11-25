"""Property 6: Card edit is atomic across multiple fields.

**Validates: Requirements 3.3, 3.10**
"""

from collections.abc import Callable
from datetime import date
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from flask_app.cards.schema import UpdateCardSchema
from flask_app.cards.service import update_card_service
from flask_app.common.exceptions import ValidationError
from flask_app.common.validation import load_schema
from tests.conftest import FakeClock

from flask_app.models import BoardMembership, Card, User  # isort: skip

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

_ALPHABET = st.characters(blacklist_categories=["Cs", "Cc", "Zs"])
_PAD = st.text(alphabet=" \t\n", max_size=5)
valid_titles = st.tuples(_PAD, st.text(alphabet=_ALPHABET, min_size=1, max_size=100), _PAD).map(
    "".join
)
valid_descriptions = st.text(alphabet=_ALPHABET, max_size=1000)
# "member" is replaced by a real Board member's id inside the test.
valid_assignees = st.sampled_from([None, "member"])
valid_due_dates = st.one_of(st.none(), st.dates(min_value=date(2000, 1, 1)).map(str))

invalid_titles = st.one_of(_PAD, st.text(alphabet=_ALPHABET, min_size=256, max_size=300))
invalid_descriptions = st.text(alphabet=_ALPHABET, min_size=5001, max_size=5050)
# A random UUID is never a member of the Board.
invalid_assignees = st.uuids().map(str)
invalid_due_dates = st.sampled_from(["not-a-date", "2025-13-45", "2025-02-30", "", 20250101])

_VALID: dict[str, st.SearchStrategy[Any]] = {
    "title": valid_titles,
    "description": valid_descriptions,
    "assignee_id": valid_assignees,
    "due_date": valid_due_dates,
}
_INVALID: dict[str, st.SearchStrategy[Any]] = {
    "title": invalid_titles,
    "description": invalid_descriptions,
    "assignee_id": invalid_assignees,
    "due_date": invalid_due_dates,
}

valid_payloads = st.fixed_dictionaries({}, optional=_VALID)

MakeUser = Callable[..., User]
MakeCard = Callable[..., Card]


@st.composite
def invalid_payloads(draw: st.DrawFn) -> dict[str, Any]:
    """Valid multi-field payload with at least one invalid field."""
    payload: dict[str, Any] = draw(valid_payloads)
    bad_fields = draw(st.sets(st.sampled_from(sorted(_INVALID)), min_size=1))
    for field in bad_fields:
        payload[field] = draw(_INVALID[field])
    return payload


def _snapshot(card: Card) -> dict[str, Any]:
    return {
        "title": card.title,
        "description": card.description,
        "assignee_id": card.assignee_id,
        "due_date": card.due_date,
        "version": card.version,
        "updated_at": card.updated_at,
    }


def _edit(card: Card, payload: dict[str, Any], member: User, actor: User) -> dict[str, Any]:
    body = {k: (member.id.hex if v == "member" else v) for k, v in payload.items()}
    body["version"] = card.version
    return update_card_service(card.id, load_schema(UpdateCardSchema(), body), actor)


# Feature: task-management-app, Property 6: Card edit is atomic across multiple fields
@_SETTINGS
@given(payload=valid_payloads)
def test_valid_multi_field_edit_persists_all_fields(
    db_session: Any,
    clock: FakeClock,
    make_user: MakeUser,
    make_board: Callable[..., Any],
    make_column: Callable[..., Any],
    make_card: MakeCard,
    payload: dict[str, Any],
) -> None:
    owner = make_user()
    member = make_user()
    board = make_board(admin=owner)
    db_session.add(BoardMembership(board_id=board.id, user_id=member.id, role="member"))
    db_session.flush()
    card = make_card(column=make_column(board=board), title="Old", description="Old text")
    before = _snapshot(card)
    clock.advance(seconds=1)

    result = _edit(card, payload, member, owner)

    expected = dict(before)
    for field, value in payload.items():
        if field == "title":
            expected[field] = value.strip()
        elif field == "assignee_id":
            expected[field] = member.id if value == "member" else None
        elif field == "due_date":
            expected[field] = date.fromisoformat(value) if value else None
        else:
            expected[field] = value
    expected["version"] = before["version"] + 1
    expected["updated_at"] = clock.now
    db_session.expire_all()
    stored = _snapshot(db_session.get(Card, card.id))
    assert stored == expected
    assert result["version"] == expected["version"]
    assert result["updated_at"] == clock.now
    assert stored["updated_at"] > before["updated_at"]


# Feature: task-management-app, Property 6: Card edit is atomic across multiple fields
@_SETTINGS
@given(payload=invalid_payloads())
def test_any_invalid_field_rejects_and_leaves_card_unchanged(
    db_session: Any,
    clock: FakeClock,
    make_user: MakeUser,
    make_board: Callable[..., Any],
    make_column: Callable[..., Any],
    make_card: MakeCard,
    payload: dict[str, Any],
) -> None:
    owner = make_user()
    member = make_user()
    board = make_board(admin=owner)
    db_session.add(BoardMembership(board_id=board.id, user_id=member.id, role="member"))
    db_session.flush()
    card = make_card(column=make_column(board=board), title="Old", description="Old text")
    before = _snapshot(card)
    clock.advance(seconds=1)

    with pytest.raises(ValidationError):
        _edit(card, payload, member, owner)

    db_session.expire_all()
    assert _snapshot(db_session.get(Card, card.id)) == before

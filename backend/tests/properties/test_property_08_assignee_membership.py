"""Property 8: Assignment requires Board membership.

**Validates: Requirements 3.4, 3.8**
"""

from collections.abc import Callable
from typing import Any
from uuid import uuid4

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from flask_app.cards.service import update_card_service
from flask_app.common.exceptions import ValidationError

from flask_app.models import BoardMembership, Card, TeamMembership, User  # isort: skip

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

MakeUser = Callable[..., User]

_MEMBER_ROLES = st.sampled_from(["admin", "member"])
_NON_MEMBER_KINDS = st.sampled_from(["team_only", "outsider", "removed", "random_id"])


# Feature: task-management-app, Property 8: Assignment requires board membership
@_SETTINGS
@given(role=_MEMBER_ROLES, reassign=st.booleans())
def test_assigning_current_board_member_succeeds(
    db_session: Any,
    make_user: MakeUser,
    make_board: Callable[..., Any],
    make_column: Callable[..., Any],
    make_card: Callable[..., Card],
    role: str,
    reassign: bool,
) -> None:
    owner = make_user()
    candidate = make_user()
    board = make_board(admin=owner)
    db_session.add(BoardMembership(board_id=board.id, user_id=candidate.id, role=role))
    db_session.flush()
    previous = make_user() if reassign else None
    card = make_card(column=make_column(board=board), assignee=previous)
    version = card.version

    result = update_card_service(card.id, {"assignee_id": candidate.id, "version": version}, owner)

    db_session.expire_all()
    stored = db_session.get(Card, card.id)
    assert stored.assignee_id == candidate.id
    assert stored.version == version + 1
    assert result["assignee_id"] == candidate.id


# Feature: task-management-app, Property 8: Assignment requires board membership
@_SETTINGS
@given(kind=_NON_MEMBER_KINDS, has_assignee=st.booleans())
def test_assigning_non_member_is_rejected_and_card_unchanged(
    db_session: Any,
    make_user: MakeUser,
    make_board: Callable[..., Any],
    make_column: Callable[..., Any],
    make_card: Callable[..., Card],
    kind: str,
    has_assignee: bool,
) -> None:
    owner = make_user()
    board = make_board(admin=owner)
    current = make_user()
    db_session.add(BoardMembership(board_id=board.id, user_id=current.id, role="member"))
    db_session.flush()
    card = make_card(column=make_column(board=board), assignee=current if has_assignee else None)
    before = (card.assignee_id, card.version)

    candidate = make_user()
    if kind == "team_only":
        db_session.add(
            TeamMembership(team_id=board.team_id, user_id=candidate.id, team_role="team_regular")
        )
        db_session.flush()
        target = candidate.id
    elif kind == "removed":
        membership = BoardMembership(board_id=board.id, user_id=candidate.id, role="member")
        db_session.add(membership)
        db_session.flush()
        db_session.delete(membership)
        db_session.flush()
        target = candidate.id
    elif kind == "outsider":
        target = candidate.id
    else:
        target = uuid4()

    with pytest.raises(ValidationError) as excinfo:
        update_card_service(card.id, {"assignee_id": target, "version": card.version}, owner)

    assert excinfo.value.field == "assignee_id"
    db_session.expire_all()
    stored = db_session.get(Card, card.id)
    assert (stored.assignee_id, stored.version) == before

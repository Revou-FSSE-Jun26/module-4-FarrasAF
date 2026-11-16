"""Property 33: Board invitations require an eligible, not-already-member Team_Member.

**Validates: Requirements 10.1, 10.4, 10.5, 10.8**
"""

from collections.abc import Callable
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import select

from flask_app.access.schema import BOARD_ROLES, AddMemberSchema
from flask_app.access.service import add_member_service
from flask_app.common.exceptions import ValidationError
from flask_app.common.validation import load_schema
from flask_app.models import Board, BoardMembership, Team, TeamMembership, User

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

valid_roles = st.sampled_from(BOARD_ROLES)
invalid_roles = st.text(max_size=12).filter(lambda s: s not in BOARD_ROLES)

MakeUser = Callable[..., User]
MakeTeam = Callable[..., Team]
MakeBoard = Callable[..., Board]


def _members(db_session: Any, board: Board) -> set[tuple[Any, str]]:
    rows = db_session.scalars(
        select(BoardMembership).where(BoardMembership.board_id == board.id)
    ).all()
    return {(m.user_id, m.role) for m in rows}


def _invite(board: Board, user: User, role: str, actor: User) -> dict[str, Any]:
    payload = load_schema(AddMemberSchema(), {"user_id": str(user.id), "role": role})
    return add_member_service(board.id, payload, actor)


# Feature: task-management-app, Property 33: Board invitations require an eligible, not-already-member Team_Member  # noqa: E501
@_SETTINGS
@given(role=valid_roles)
def test_eligible_team_member_is_granted_the_specified_role(
    db_session: Any, make_user: MakeUser, make_board: MakeBoard, role: str
) -> None:
    admin = make_user()
    board = make_board(admin=admin)
    invitee = make_user()
    db_session.add(
        TeamMembership(team_id=board.team_id, user_id=invitee.id, team_role="team_regular")
    )
    db_session.flush()

    result = _invite(board, invitee, role, admin)

    assert result["user_id"] == invitee.id
    assert result["role"] == role
    assert _members(db_session, board) == {(admin.id, "admin"), (invitee.id, role)}


# Feature: task-management-app, Property 33: Board invitations require an eligible, not-already-member Team_Member  # noqa: E501
@_SETTINGS
@given(role=invalid_roles)
def test_invalid_role_is_rejected_and_membership_unchanged(
    db_session: Any, make_user: MakeUser, make_board: MakeBoard, role: str
) -> None:
    admin = make_user()
    board = make_board(admin=admin)
    invitee = make_user()
    db_session.add(
        TeamMembership(team_id=board.team_id, user_id=invitee.id, team_role="team_regular")
    )
    db_session.flush()
    before = _members(db_session, board)

    with pytest.raises(ValidationError):
        _invite(board, invitee, role, admin)

    assert _members(db_session, board) == before


# Feature: task-management-app, Property 33: Board invitations require an eligible, not-already-member Team_Member  # noqa: E501
@_SETTINGS
@given(first_role=valid_roles, second_role=valid_roles)
def test_already_member_is_rejected_and_membership_unchanged(
    db_session: Any, make_user: MakeUser, make_board: MakeBoard, first_role: str, second_role: str
) -> None:
    admin = make_user()
    board = make_board(admin=admin)
    invitee = make_user()
    db_session.add(
        TeamMembership(team_id=board.team_id, user_id=invitee.id, team_role="team_regular")
    )
    db_session.flush()
    _invite(board, invitee, first_role, admin)
    before = _members(db_session, board)

    with pytest.raises(ValidationError) as exc:
        _invite(board, invitee, second_role, admin)

    assert exc.value.field == "user_id"
    assert _members(db_session, board) == before


# Feature: task-management-app, Property 33: Board invitations require an eligible, not-already-member Team_Member  # noqa: E501
@_SETTINGS
@given(role=valid_roles, same_user_other_team=st.booleans())
def test_non_team_member_is_rejected_and_membership_unchanged(
    db_session: Any,
    make_user: MakeUser,
    make_team: MakeTeam,
    make_board: MakeBoard,
    role: str,
    same_user_other_team: bool,
) -> None:
    admin = make_user()
    board = make_board(admin=admin)
    outsider = make_user()
    if same_user_other_team:
        # Member of a different Team only: still not eligible for this Board.
        make_team(admin=outsider)
    before = _members(db_session, board)

    with pytest.raises(ValidationError) as exc:
        _invite(board, outsider, role, admin)

    assert exc.value.field == "user_id"
    assert _members(db_session, board) == before

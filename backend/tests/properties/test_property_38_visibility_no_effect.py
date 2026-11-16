"""Property 38: Visibility does not change who can access a Board.

**Validates: Requirements 1.14**
"""

from collections.abc import Callable
from typing import Any

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from flask_app.access.rbac import ROLE_CAPABILITIES, get_board_role, role_allows
from flask_app.boards.service import list_boards_service, update_board_service
from flask_app.extensions import db
from flask_app.models import Board, BoardMembership, TeamMembership, User

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

MakeUser = Callable[..., User]
MakeBoard = Callable[..., Board]

_OPERATIONS = sorted({op for ops in ROLE_CAPABILITIES.values() for op in ops})
_VISIBILITIES = st.sampled_from(["private", "team"])


def _snapshot(board: Board, users: list[User]) -> list[Any]:
    """Access decisions, stored roles, and board-list contents for each user."""
    result: list[Any] = []
    for user in users:
        role = get_board_role(board.id, user.id)
        decisions = tuple(role_allows(role, op) for op in _OPERATIONS)
        listed = {item["id"] for item in list_boards_service({}, user)["items"]}
        result.append((role, decisions, board.id in listed))
    return result


# Feature: task-management-app, Property 38: Visibility does not change who can access a Board
@_SETTINGS
@given(first=_VISIBILITIES, second=_VISIBILITIES)
def test_visibility_does_not_change_board_access(
    db_session: Any,
    make_user: MakeUser,
    make_board: MakeBoard,
    first: str,
    second: str,
) -> None:
    admin = make_user()
    member = make_user()
    team_only = make_user()
    outsider = make_user()
    board = make_board(admin=admin, visibility=first)
    db_session.add(
        TeamMembership(team_id=board.team_id, user_id=member.id, team_role="team_regular")
    )
    db_session.add(
        TeamMembership(team_id=board.team_id, user_id=team_only.id, team_role="team_regular")
    )
    db_session.add(BoardMembership(board_id=board.id, user_id=member.id, role="member"))
    db.session.flush()
    users = [admin, member, team_only, outsider]

    before = _snapshot(board, users)
    update_board_service(board.id, {"visibility": second}, admin)
    after = _snapshot(board, users)

    assert board.visibility == second
    assert before == after
    # Admin and Member are allowed; non-member Team_Member and outsider are denied.
    assert [entry[0] for entry in after] == ["admin", "member", None, None]
    assert [entry[2] for entry in after] == [True, True, False, False]

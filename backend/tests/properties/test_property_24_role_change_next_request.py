"""Property 24: Role changes apply on the next request from stored membership.

**Validates: Requirements 10.2, 10.3**
"""

from collections.abc import Callable
from typing import Any

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from flask_app.access.rbac import ROLE_CAPABILITIES, get_board_role, role_allows
from flask_app.access.schema import BOARD_ROLES
from flask_app.access.service import change_member_role_service, remove_member_service
from flask_app.models import Board, BoardMembership, TeamMembership, User

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

MakeUser = Callable[..., User]
MakeBoard = Callable[..., Board]

ALL_OPERATIONS = frozenset().union(*ROLE_CAPABILITIES.values())


def _assert_decisions(board: Board, user: User, expected_role: str | None) -> None:
    """The next authorization decision must come from the stored membership."""
    assert get_board_role(board.id, user.id) == expected_role
    allowed = ROLE_CAPABILITIES[expected_role] if expected_role else frozenset()
    for operation in ALL_OPERATIONS:
        assert role_allows(get_board_role(board.id, user.id), operation) == (operation in allowed)


# Feature: task-management-app, Property 24: Role changes apply on the next request from stored membership  # noqa: E501
@_SETTINGS
@given(
    initial=st.sampled_from(BOARD_ROLES),
    changes=st.lists(st.sampled_from(BOARD_ROLES), max_size=6),
    remove_at_end=st.booleans(),
)
def test_role_change_or_removal_applies_on_next_decision(
    db_session: Any,
    make_user: MakeUser,
    make_board: MakeBoard,
    initial: str,
    changes: list[str],
    remove_at_end: bool,
) -> None:
    creator = make_user()
    board = make_board(admin=creator)
    target = make_user()
    db_session.add(
        TeamMembership(team_id=board.team_id, user_id=target.id, team_role="team_regular")
    )
    db_session.add(BoardMembership(board_id=board.id, user_id=target.id, role=initial))
    db_session.flush()
    _assert_decisions(board, target, initial)

    # The creator stays Admin, so the last-Admin rule never interferes.
    for new_role in changes:
        change_member_role_service(board.id, target.id, {"role": new_role})
        _assert_decisions(board, target, new_role)

    if remove_at_end:
        # An Admin cannot be removed (R10.10), so demote first, as the UI requires.
        if (changes[-1] if changes else initial) == "admin":
            change_member_role_service(board.id, target.id, {"role": "member"})
            _assert_decisions(board, target, "member")
        remove_member_service(board.id, target.id, creator)
        _assert_decisions(board, target, None)

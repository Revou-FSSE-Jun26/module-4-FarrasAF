"""Property 23: Board retains at least one Admin.

**Validates: Requirements 10.6, 10.10**
"""

from collections.abc import Callable
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import select

from flask_app.access.schema import BOARD_ROLES
from flask_app.access.service import change_member_role_service, remove_member_service
from flask_app.common.exceptions import NotFoundError, ValidationError
from flask_app.models import Board, BoardMembership, TeamMembership, User

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

POOL_SIZE = 4

MakeUser = Callable[..., User]
MakeBoard = Callable[..., Board]

initial_roles = st.lists(
    st.sampled_from(BOARD_ROLES), min_size=POOL_SIZE - 1, max_size=POOL_SIZE - 1
)
operations = st.lists(
    st.tuples(
        st.sampled_from(["change", "remove"]),
        st.integers(min_value=0, max_value=POOL_SIZE - 1),
        st.sampled_from(BOARD_ROLES),
    ),
    min_size=1,
    max_size=15,
)


def _members(db_session: Any, board: Board) -> dict[Any, str]:
    rows = db_session.scalars(
        select(BoardMembership).where(BoardMembership.board_id == board.id)
    ).all()
    return {m.user_id: m.role for m in rows}


# Feature: task-management-app, Property 23: Board retains at least one Admin
@_SETTINGS
@given(roles=initial_roles, ops=operations)
def test_board_always_retains_an_admin_and_rejections_change_nothing(
    db_session: Any,
    make_user: MakeUser,
    make_board: MakeBoard,
    roles: list[str],
    ops: list[tuple[str, int, str]],
) -> None:
    creator = make_user()
    board = make_board(admin=creator)
    pool = [creator]
    for role in roles:
        user = make_user()
        db_session.add(
            TeamMembership(team_id=board.team_id, user_id=user.id, team_role="team_regular")
        )
        db_session.add(BoardMembership(board_id=board.id, user_id=user.id, role=role))
        pool.append(user)
    db_session.flush()

    for kind, index, new_role in ops:
        target = pool[index]
        before = _members(db_session, board)
        admins = [uid for uid, role in before.items() if role == "admin"]
        is_member = target.id in before
        is_admin = is_member and before[target.id] == "admin"
        # An Admin can never be removed (R10.10); a role change must keep one Admin (R10.6).
        would_orphan = is_admin and (kind == "remove" or (len(admins) == 1 and new_role != "admin"))

        if not is_member:
            with pytest.raises(NotFoundError):
                if kind == "change":
                    change_member_role_service(board.id, target.id, {"role": new_role})
                else:
                    remove_member_service(board.id, target.id, creator)
            assert _members(db_session, board) == before
        elif would_orphan:
            with pytest.raises(ValidationError):
                if kind == "change":
                    change_member_role_service(board.id, target.id, {"role": new_role})
                else:
                    remove_member_service(board.id, target.id, creator)
            assert _members(db_session, board) == before
        else:
            expected = dict(before)
            if kind == "change":
                change_member_role_service(board.id, target.id, {"role": new_role})
                expected[target.id] = new_role
            else:
                remove_member_service(board.id, target.id, creator)
                del expected[target.id]
            assert _members(db_session, board) == expected

        assert "admin" in _members(db_session, board).values()

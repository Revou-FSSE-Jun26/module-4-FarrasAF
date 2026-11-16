"""Property 32: Board creation grants the creator Admin effective immediately.

**Validates: Requirements 1.1, 1.11, 1.12**
"""

from collections.abc import Callable
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import func, select

from flask_app.access.rbac import BOARD_ADMIN, COLUMN_MANAGE, get_board_role, role_allows
from flask_app.boards.schema import CreateBoardSchema
from flask_app.boards.service import DEFAULT_COLUMNS, create_board_service
from flask_app.common.exceptions import AuthorizationError
from flask_app.common.validation import load_schema
from flask_app.extensions import db
from flask_app.models import Board, BoardMembership, Column, Team, User

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

_TEXT = st.text(alphabet=st.characters(blacklist_categories=["Cs", "Cc", "Zs"]), min_size=1)
_PAD = st.text(alphabet=" \t\n", max_size=5)
valid_names = st.tuples(_PAD, _TEXT.filter(lambda s: len(s) <= 100), _PAD).map("".join)

MakeUser = Callable[..., User]
MakeTeam = Callable[..., Team]


def _create(team: Team, name: str, user: User) -> dict[str, Any]:
    payload = load_schema(CreateBoardSchema(), {"team_id": str(team.id), "name": name})
    return create_board_service(payload, user)


def _board_count() -> int:
    return int(db.session.scalar(select(func.count()).select_from(Board)) or 0)


# Feature: task-management-app, Property 32: Board creation grants the creator Admin effective immediately  # noqa: E501
@_SETTINGS
@given(name=valid_names)
def test_team_member_creates_board_as_admin_effective_immediately(
    db_session: Any, make_user: MakeUser, make_team: MakeTeam, name: str
) -> None:
    creator = make_user()
    team = make_team(admin=creator)

    board = _create(team, name, creator)

    assert board["name"] == name.strip()
    assert board["team_id"] == team.id
    assert board["current_user_role"] == "admin"

    membership = db_session.scalar(
        select(BoardMembership).where(
            BoardMembership.board_id == board["id"], BoardMembership.user_id == creator.id
        )
    )
    assert membership is not None
    assert membership.role == "admin"

    columns = db_session.scalars(
        select(Column).where(Column.board_id == board["id"]).order_by(Column.order_index)
    ).all()
    assert [c.name for c in columns] == list(DEFAULT_COLUMNS)
    assert [c.order_index for c in columns] == [0, 1, 2]

    # The very next request resolves the role from stored membership: Admin-only
    # operations are allowed with no re-login or token refresh.
    role = get_board_role(board["id"], creator.id)
    assert role == "admin"
    assert role_allows(role, COLUMN_MANAGE)
    assert role_allows(role, BOARD_ADMIN)


# Feature: task-management-app, Property 32: Board creation grants the creator Admin effective immediately  # noqa: E501
@_SETTINGS
@given(name=valid_names)
def test_non_team_member_is_rejected_and_creates_no_board(
    db_session: Any, make_user: MakeUser, make_team: MakeTeam, name: str
) -> None:
    team = make_team(admin=make_user())
    outsider = make_user()
    before = _board_count()

    with pytest.raises(AuthorizationError):
        _create(team, name, outsider)

    assert _board_count() == before
    assert (
        db_session.scalar(
            select(func.count())
            .select_from(BoardMembership)
            .where(BoardMembership.user_id == outsider.id)
        )
        == 0
    )

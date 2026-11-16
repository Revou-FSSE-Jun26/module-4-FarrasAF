"""Property 31: Team creation, listing, membership, and access control.

**Validates: Requirements 16.1, 16.2, 16.3, 16.4, 16.5**
"""

import uuid
from collections.abc import Callable
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import func, select

from flask_app.common.exceptions import AuthorizationError, ValidationError
from flask_app.common.validation import load_schema
from flask_app.extensions import db
from flask_app.models import Team, TeamMembership, User
from flask_app.teams.schema import CreateTeamSchema
from flask_app.teams.service import (
    TEAM_ADMIN,
    TEAM_REGULAR,
    accept_join_link_service,
    create_team_service,
    generate_join_link_service,
    list_members_service,
    list_teams_service,
)

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

_TEXT = st.text(alphabet=st.characters(blacklist_categories=["Cs", "Cc", "Zs"]), min_size=1)
_PAD = st.text(alphabet=" \t\n", max_size=5)
valid_names = st.tuples(_PAD, _TEXT.filter(lambda s: len(s) <= 100), _PAD).map("".join)
blank_names = st.text(alphabet=" \t\n", max_size=10)
too_long_names = _TEXT.filter(lambda s: len(s) >= 1).flatmap(
    lambda s: st.just(("x" + s) * 101)  # always > 100 chars after trimming
)

MakeUser = Callable[..., User]


def _create(name: str, user: User) -> dict[str, Any]:
    return create_team_service(load_schema(CreateTeamSchema(), {"name": name}), user)


def _team_count() -> int:
    return int(db.session.scalar(select(func.count()).select_from(Team)) or 0)


# Feature: task-management-app, Property 31: Team creation, listing, membership, and access control
@_SETTINGS
@given(name=valid_names)
def test_valid_name_creates_team_with_creator_as_team_admin(
    db_session: Any, make_user: MakeUser, name: str
) -> None:
    creator = make_user()
    team = _create(name, creator)

    assert team["name"] == name.strip()
    assert team["current_user_team_role"] == TEAM_ADMIN
    membership = db_session.scalar(
        select(TeamMembership).where(
            TeamMembership.team_id == team["id"], TeamMembership.user_id == creator.id
        )
    )
    assert membership is not None
    assert membership.team_role == TEAM_ADMIN


# Feature: task-management-app, Property 31: Team creation, listing, membership, and access control
@_SETTINGS
@given(name=st.one_of(blank_names, too_long_names))
def test_invalid_name_is_rejected_and_creates_no_team(
    db_session: Any, make_user: MakeUser, name: str
) -> None:
    creator = make_user()
    before = _team_count()
    with pytest.raises(ValidationError) as caught:
        _create(name, creator)
    assert caught.value.field == "name"
    assert _team_count() == before


# Feature: task-management-app, Property 31: Team creation, listing, membership, and access control
@_SETTINGS
@given(
    own_count=st.integers(min_value=0, max_value=3),
    joined_count=st.integers(min_value=0, max_value=3),
    other_count=st.integers(min_value=0, max_value=3),
)
def test_list_returns_exactly_the_users_teams(
    db_session: Any,
    make_user: MakeUser,
    own_count: int,
    joined_count: int,
    other_count: int,
) -> None:
    user = make_user()
    other = make_user()
    expected = {_create("own", user)["id"] for _ in range(own_count)}
    for _ in range(joined_count):
        team = _create("joined", other)
        link = generate_join_link_service(team["id"], other)
        accept_join_link_service(link["token"], user)
        expected.add(team["id"])
    for _ in range(other_count):
        _create("foreign", other)

    listed = list_teams_service(user)["items"]
    assert {t["id"] for t in listed} == expected
    assert len(listed) == len(expected)


# Feature: task-management-app, Property 31: Team creation, listing, membership, and access control
@_SETTINGS
@given(
    names=st.lists(
        st.text(min_size=1, max_size=50, alphabet="abcdefghij "), min_size=0, max_size=4
    ),
    name=valid_names,
)
def test_members_listed_for_member_and_denied_for_non_member(
    db_session: Any, make_user: MakeUser, names: list[str], name: str
) -> None:
    admin = make_user(display_name="Admin")
    outsider = make_user()
    team = _create(name, admin)
    expected: dict[uuid.UUID, tuple[str, str]] = {admin.id: ("Admin", TEAM_ADMIN)}
    for display in names:
        member = make_user(display_name=display)
        link = generate_join_link_service(team["id"], admin)
        accept_join_link_service(link["token"], member)
        expected[member.id] = (display, TEAM_REGULAR)

    for viewer in [admin, db_session.get(User, next(iter(expected)))]:
        items = list_members_service(team["id"], viewer)["items"]
        assert {i["user_id"]: (i["display_name"], i["team_role"]) for i in items} == expected
        assert len(items) == len(expected)
        assert all(set(i) == {"user_id", "display_name", "team_role"} for i in items)

    with pytest.raises(AuthorizationError):
        list_members_service(team["id"], outsider)

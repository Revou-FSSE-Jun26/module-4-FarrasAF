"""Unit tests for the teams service (R16.1, R16.5, R17.3, R17.4, R17.8, R17.9)."""

from collections.abc import Callable
from typing import Any

import pytest
from sqlalchemy import select

from flask_app.common.exceptions import AuthorizationError, ValidationError
from flask_app.models import Team, TeamMembership, User
from flask_app.teams.service import (
    accept_join_link_service,
    create_team_service,
    generate_join_link_service,
    list_members_service,
    list_teams_service,
    preview_join_link_service,
)
from tests.conftest import FakeClock


def test_create_team_makes_creator_team_admin(
    db_session: Any, make_user: Callable[..., User]
) -> None:
    creator = make_user()
    result = create_team_service({"name": "Alpha"}, creator)
    assert result["current_user_team_role"] == "team_admin"
    membership = db_session.scalar(
        select(TeamMembership).where(
            TeamMembership.team_id == result["id"], TeamMembership.user_id == creator.id
        )
    )
    assert membership is not None
    assert membership.team_role == "team_admin"


def test_accept_join_link_adds_team_regular(
    db_session: Any, make_user: Callable[..., User], make_team: Callable[..., Team]
) -> None:
    admin = make_user()
    team = make_team(admin=admin)
    joiner = make_user()
    link = generate_join_link_service(team.id, admin)
    result = accept_join_link_service(link["token"], joiner)
    assert result["team_id"] == team.id
    membership = db_session.scalar(
        select(TeamMembership).where(
            TeamMembership.team_id == team.id, TeamMembership.user_id == joiner.id
        )
    )
    assert membership is not None
    assert membership.team_role == "team_regular"


def test_expired_join_link_is_rejected(
    db_session: Any,
    clock: FakeClock,
    make_user: Callable[..., User],
    make_team: Callable[..., Team],
) -> None:
    admin = make_user()
    team = make_team(admin=admin)
    link = generate_join_link_service(team.id, admin)
    clock.advance(days=7, seconds=1)
    with pytest.raises(ValidationError):
        accept_join_link_service(link["token"], make_user())
    with pytest.raises(ValidationError):
        preview_join_link_service(link["token"])


def test_non_member_cannot_list_members(
    db_session: Any, make_user: Callable[..., User], make_team: Callable[..., Team]
) -> None:
    team = make_team()
    with pytest.raises(AuthorizationError):
        list_members_service(team.id, make_user())


def test_preview_returns_only_team_name(
    db_session: Any, make_user: Callable[..., User], make_team: Callable[..., Team]
) -> None:
    admin = make_user()
    team = make_team(name="Secret Squad", admin=admin)
    link = generate_join_link_service(team.id, admin)
    assert preview_join_link_service(link["token"]) == {"team_name": "Secret Squad"}


def test_list_teams_shape_and_roles(
    db_session: Any, make_user: Callable[..., User], make_team: Callable[..., Team]
) -> None:
    user = make_user()
    own = make_team(name="Own", admin=user)
    other_admin = make_user()
    joined = make_team(name="Joined", admin=other_admin)
    make_team(name="Unrelated")
    accept_join_link_service(generate_join_link_service(joined.id, other_admin)["token"], user)

    result = list_teams_service(user)

    assert set(result) == {"items"}
    items = {item["name"]: item for item in result["items"]}
    assert set(items) == {"Own", "Joined"}
    for item in items.values():
        assert set(item) == {"id", "name", "current_user_team_role", "created_at"}
    assert items["Own"]["id"] == own.id
    assert items["Own"]["current_user_team_role"] == "team_admin"
    assert items["Joined"]["current_user_team_role"] == "team_regular"

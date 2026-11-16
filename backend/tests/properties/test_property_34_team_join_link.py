"""Property 34: Team_Join_Link lifecycle and access control.

**Validates: Requirements 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7**
"""

from collections.abc import Callable
from datetime import timedelta
from typing import Any
from uuid import UUID

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import func, select

from flask_app.common.exceptions import AuthorizationError, ValidationError
from flask_app.extensions import db
from flask_app.models import Team, TeamMembership, User
from flask_app.teams.service import (
    JOIN_LINK_LIFETIME,
    TEAM_REGULAR,
    accept_join_link_service,
    generate_join_link_service,
    list_join_links_service,
    revoke_join_link_service,
)
from tests.conftest import FakeClock

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

MakeUser = Callable[..., User]
MakeTeam = Callable[..., Team]

_INVALID_MESSAGE = "Team join link is invalid"
_SEVEN_DAYS = timedelta(days=7)


def _membership_count(team_id: UUID) -> int:
    return int(
        db.session.scalar(
            select(func.count())
            .select_from(TeamMembership)
            .where(TeamMembership.team_id == team_id)
        )
        or 0
    )


def _membership_of(team_id: UUID, user: User) -> TeamMembership | None:
    return db.session.scalar(
        select(TeamMembership).where(
            TeamMembership.team_id == team_id, TeamMembership.user_id == user.id
        )
    )


def _statuses(team_id: UUID, admin: User) -> dict[str, str]:
    items = list_join_links_service(team_id, admin)["items"]
    return {item["token"]: item["status"] for item in items}


# Feature: task-management-app, Property 34: Team_Join_Link lifecycle and access control
@_SETTINGS
@given(count=st.integers(min_value=1, max_value=5), offset=st.integers(0, 10**6))
def test_generated_links_are_active_expire_in_7_days_and_tokens_unique(
    db_session: Any,
    clock: FakeClock,
    make_user: MakeUser,
    make_team: MakeTeam,
    count: int,
    offset: int,
) -> None:
    clock.advance(seconds=offset)
    admin = make_user()
    team = make_team(admin=admin)

    links = [generate_join_link_service(team.id, admin) for _ in range(count)]

    assert JOIN_LINK_LIFETIME == _SEVEN_DAYS
    for link in links:
        assert link["status"] == "active"
        assert link["team_id"] == team.id
        assert link["expires_at"] == clock.now + _SEVEN_DAYS
        assert link["is_expired"] is False
        assert len(link["token"]) >= 43  # 32 random bytes, urlsafe base64
    tokens = [link["token"] for link in links]
    assert len(set(tokens)) == count
    assert set(_statuses(team.id, admin)) == set(tokens)


# Feature: task-management-app, Property 34: Team_Join_Link lifecycle and access control
@_SETTINGS
@given(as_member=st.booleans())
def test_only_team_admin_can_generate_list_and_revoke(
    db_session: Any,
    clock: FakeClock,
    make_user: MakeUser,
    make_team: MakeTeam,
    as_member: bool,
) -> None:
    admin = make_user()
    team = make_team(admin=admin)
    link = generate_join_link_service(team.id, admin)

    actor = make_user()
    if as_member:
        accept_join_link_service(link["token"], actor)
        assert _membership_of(team.id, actor) is not None  # Team_Regular, not admin

    with pytest.raises(AuthorizationError):
        generate_join_link_service(team.id, actor)
    with pytest.raises(AuthorizationError):
        list_join_links_service(team.id, actor)
    with pytest.raises(AuthorizationError):
        revoke_join_link_service(link["token"], actor)

    assert _statuses(team.id, admin) == {link["token"]: "active"}


# Feature: task-management-app, Property 34: Team_Join_Link lifecycle and access control
@_SETTINGS
@given(count=st.integers(min_value=2, max_value=5), data=st.data())
def test_revoking_affects_only_that_link(
    db_session: Any,
    clock: FakeClock,
    make_user: MakeUser,
    make_team: MakeTeam,
    count: int,
    data: st.DataObject,
) -> None:
    admin = make_user()
    team = make_team(admin=admin)
    tokens = [generate_join_link_service(team.id, admin)["token"] for _ in range(count)]
    revoked = data.draw(st.sampled_from(tokens))

    result = revoke_join_link_service(revoked, admin)

    assert result["status"] == "inactive"
    statuses = _statuses(team.id, admin)
    assert statuses[revoked] == "inactive"
    assert all(status == "active" for token, status in statuses.items() if token != revoked)

    # Other links still work, the revoked one does not.
    joiner = make_user()
    other = data.draw(st.sampled_from([t for t in tokens if t != revoked]))
    accept_join_link_service(other, joiner)
    assert _membership_of(team.id, joiner) is not None
    with pytest.raises(ValidationError):
        accept_join_link_service(revoked, make_user())


# Feature: task-management-app, Property 34: Team_Join_Link lifecycle and access control
@_SETTINGS
@given(elapsed=st.timedeltas(min_value=timedelta(0), max_value=_SEVEN_DAYS - timedelta(seconds=1)))
def test_accepting_active_unexpired_link_makes_user_team_regular(
    db_session: Any,
    clock: FakeClock,
    make_user: MakeUser,
    make_team: MakeTeam,
    elapsed: timedelta,
) -> None:
    admin = make_user()
    team = make_team(admin=admin)
    link = generate_join_link_service(team.id, admin)
    joiner = make_user()
    before = _membership_count(team.id)

    clock.advance(seconds=elapsed.total_seconds())
    result = accept_join_link_service(link["token"], joiner)

    assert result["team_id"] == team.id
    membership = _membership_of(team.id, joiner)
    assert membership is not None
    assert membership.team_role == TEAM_REGULAR
    assert _membership_count(team.id) == before + 1


# Feature: task-management-app, Property 34: Team_Join_Link lifecycle and access control
@_SETTINGS
@given(
    kind=st.sampled_from(["expired", "revoked", "unknown"]),
    past_expiry=st.timedeltas(min_value=timedelta(0), max_value=timedelta(days=30)),
    unknown_token=st.text(min_size=0, max_size=80),
)
def test_expired_revoked_or_unknown_links_are_rejected_without_membership(
    db_session: Any,
    clock: FakeClock,
    make_user: MakeUser,
    make_team: MakeTeam,
    kind: str,
    past_expiry: timedelta,
    unknown_token: str,
) -> None:
    admin = make_user()
    team = make_team(admin=admin)
    link = generate_join_link_service(team.id, admin)
    joiner = make_user()
    before = _membership_count(team.id)

    token = link["token"]
    if kind == "expired":
        clock.advance(seconds=(_SEVEN_DAYS + past_expiry).total_seconds())
    elif kind == "revoked":
        revoke_join_link_service(token, admin)
    else:
        token = unknown_token if unknown_token != token else unknown_token + "x"

    with pytest.raises(ValidationError) as caught:
        accept_join_link_service(token, joiner)

    assert caught.value.message == _INVALID_MESSAGE
    assert _membership_of(team.id, joiner) is None
    assert _membership_count(team.id) == before


# Feature: task-management-app, Property 34: Team_Join_Link lifecycle and access control
@_SETTINGS
@given(as_admin=st.booleans())
def test_accept_by_existing_member_is_rejected(
    db_session: Any,
    clock: FakeClock,
    make_user: MakeUser,
    make_team: MakeTeam,
    as_admin: bool,
) -> None:
    admin = make_user()
    team = make_team(admin=admin)
    link = generate_join_link_service(team.id, admin)
    member = admin
    if not as_admin:
        member = make_user()
        accept_join_link_service(link["token"], member)
    role_before = _membership_of(team.id, member)
    assert role_before is not None
    expected_role = role_before.team_role
    before = _membership_count(team.id)

    with pytest.raises(ValidationError):
        accept_join_link_service(link["token"], member)

    after = _membership_of(team.id, member)
    assert after is not None
    assert after.team_role == expected_role
    assert _membership_count(team.id) == before

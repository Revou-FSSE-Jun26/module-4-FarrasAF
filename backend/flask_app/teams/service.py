import secrets
from datetime import timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select

from flask_app.common.exceptions import AuthorizationError, NotFoundError, ValidationError
from flask_app.common.time import utc_now
from flask_app.extensions import db
from flask_app.models import Team, TeamJoinLink, TeamMembership, User

TEAM_ADMIN = "team_admin"
TEAM_REGULAR = "team_regular"
JOIN_LINK_LIFETIME = timedelta(days=7)
_INVALID_LINK = "Team join link is invalid"


def _team_dict(team: Team, role: str) -> dict[str, Any]:
    return {
        "id": team.id,
        "name": team.name,
        "current_user_team_role": role,
        "created_at": team.created_at,
    }


def _link_dict(link: TeamJoinLink) -> dict[str, Any]:
    return {
        "id": link.id,
        "team_id": link.team_id,
        "token": link.token,
        "status": link.status,
        "expires_at": link.expires_at,
        "created_at": link.created_at,
        "is_expired": link.expires_at <= utc_now(),
    }


def _get_membership(team_id: UUID, user: User) -> TeamMembership | None:
    """Team_Role is always read from the stored membership."""
    return db.session.scalar(
        select(TeamMembership).where(
            TeamMembership.team_id == team_id, TeamMembership.user_id == user.id
        )
    )


def _require_member(team_id: UUID, user: User) -> TeamMembership:
    membership = _get_membership(team_id, user)
    if membership is None:
        raise AuthorizationError("You are not a member of this team")
    return membership


def _require_admin(team_id: UUID, user: User) -> None:
    if _require_member(team_id, user).team_role != TEAM_ADMIN:
        raise AuthorizationError("Only the team admin can manage join links")


def _get_valid_link(token: str) -> TeamJoinLink:
    if "\x00" in token:
        raise ValidationError(_INVALID_LINK)
    link: TeamJoinLink | None = db.session.scalar(
        select(TeamJoinLink).where(TeamJoinLink.token == token)
    )
    if link is None or link.status != "active" or link.expires_at <= utc_now():
        raise ValidationError(_INVALID_LINK)
    return link


def create_team_service(payload: dict[str, Any], user: User) -> dict[str, Any]:
    team = Team(name=payload["name"])
    db.session.add(team)
    db.session.flush()
    db.session.add(TeamMembership(team_id=team.id, user_id=user.id, team_role=TEAM_ADMIN))
    db.session.commit()
    return _team_dict(team, TEAM_ADMIN)


def list_teams_service(user: User) -> dict[str, Any]:
    rows = db.session.execute(
        select(Team, TeamMembership.team_role)
        .join(TeamMembership, TeamMembership.team_id == Team.id)
        .where(TeamMembership.user_id == user.id)
        .order_by(Team.created_at, Team.id)
    ).all()
    return {"items": [_team_dict(team, role) for team, role in rows]}


def list_members_service(team_id: UUID, user: User) -> dict[str, Any]:
    _require_member(team_id, user)
    rows = db.session.execute(
        select(TeamMembership.user_id, User.display_name, TeamMembership.team_role)
        .join(User, User.id == TeamMembership.user_id)
        .where(TeamMembership.team_id == team_id)
        .order_by(TeamMembership.created_at, TeamMembership.id)
    ).all()
    return {
        "items": [
            {"user_id": uid, "display_name": name, "team_role": role} for uid, name, role in rows
        ]
    }


def generate_join_link_service(team_id: UUID, user: User) -> dict[str, Any]:
    _require_admin(team_id, user)
    link = TeamJoinLink(
        team_id=team_id,
        token=secrets.token_urlsafe(32),
        status="active",
        expires_at=utc_now() + JOIN_LINK_LIFETIME,
        created_by_id=user.id,
    )
    db.session.add(link)
    db.session.commit()
    return _link_dict(link)


def list_join_links_service(team_id: UUID, user: User) -> dict[str, Any]:
    _require_admin(team_id, user)
    links = db.session.scalars(
        select(TeamJoinLink)
        .where(TeamJoinLink.team_id == team_id)
        .order_by(TeamJoinLink.created_at.desc(), TeamJoinLink.id.desc())
    ).all()
    return {"items": [_link_dict(link) for link in links]}


def revoke_join_link_service(token: str, user: User) -> dict[str, Any]:
    link = db.session.scalar(select(TeamJoinLink).where(TeamJoinLink.token == token))
    if link is None:
        raise NotFoundError("Team join link not found")
    _require_admin(link.team_id, user)
    link.status = "inactive"
    db.session.commit()
    return _link_dict(link)


def preview_join_link_service(token: str) -> dict[str, Any]:
    link = _get_valid_link(token)
    return {"team_name": link.team.name}


def accept_join_link_service(token: str, user: User) -> dict[str, Any]:
    link = _get_valid_link(token)
    if _get_membership(link.team_id, user) is not None:
        raise ValidationError("You are already a member of this team")
    db.session.add(TeamMembership(team_id=link.team_id, user_id=user.id, team_role=TEAM_REGULAR))
    db.session.commit()
    return {"team_id": link.team_id}

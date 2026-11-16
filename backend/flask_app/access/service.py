"""Access_Control_Service: Board member and Invitation_Link management."""

import secrets
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from flask_app.access.rbac import get_board_role, role_allows
from flask_app.activity.service import record_activity
from flask_app.common.exceptions import AuthorizationError, NotFoundError, ValidationError
from flask_app.extensions import db
from flask_app.models import Board, BoardMembership, InvitationLink, TeamMembership, User


def _member_to_dict(membership: BoardMembership, display_name: str) -> dict[str, Any]:
    return {
        "user_id": membership.user_id,
        "display_name": display_name,
        "role": membership.role,
    }


def _lock_board(board_id: UUID) -> Board:
    """Lock the Board row so concurrent member changes cannot interleave."""
    board = db.session.scalars(select(Board).where(Board.id == board_id).with_for_update()).first()
    if board is None:
        raise NotFoundError("Board not found")
    return board


def _get_membership(board_id: UUID, user_id: UUID) -> BoardMembership:
    membership = db.session.scalars(
        select(BoardMembership).where(
            BoardMembership.board_id == board_id, BoardMembership.user_id == user_id
        )
    ).first()
    if membership is None:
        raise NotFoundError("Member not found")
    return membership


def _admin_count(board_id: UUID) -> int:
    count = db.session.scalar(
        select(func.count())
        .select_from(BoardMembership)
        .where(BoardMembership.board_id == board_id, BoardMembership.role == "admin")
    )
    return int(count or 0)


def list_members_service(board_id: UUID) -> dict[str, Any]:
    """All Board members with their stored role, ordered by display name."""
    rows = db.session.scalars(
        select(BoardMembership)
        .options(joinedload(BoardMembership.user))  # type: ignore[arg-type]
        .where(BoardMembership.board_id == board_id)
        .order_by(BoardMembership.created_at, BoardMembership.id)
    ).all()
    return {"items": [_member_to_dict(m, m.user.display_name) for m in rows]}


def add_member_service(board_id: UUID, payload: dict[str, Any], actor: User) -> dict[str, Any]:
    """Grant a Team_Member of the Board's Team a role on the Board."""
    board = _lock_board(board_id)
    user_id: UUID = payload["user_id"]
    user = db.session.get(User, user_id)
    is_team_member = (
        user is not None
        and db.session.scalar(
            select(func.count())
            .select_from(TeamMembership)
            .where(TeamMembership.team_id == board.team_id, TeamMembership.user_id == user_id)
        )
        == 1
    )
    if user is None or not is_team_member:
        raise ValidationError("User is not a Team_Member of the Board's Team", field="user_id")
    exists = db.session.scalar(
        select(func.count())
        .select_from(BoardMembership)
        .where(BoardMembership.board_id == board_id, BoardMembership.user_id == user_id)
    )
    if exists:
        raise ValidationError("User is already a Member of the Board", field="user_id")
    membership = BoardMembership(board_id=board_id, user_id=user_id, role=payload["role"])
    db.session.add(membership)
    record_activity(board_id, actor.id, "member_joined", user_id)
    db.session.commit()
    return _member_to_dict(membership, user.display_name)


def change_member_role_service(
    board_id: UUID, user_id: UUID, payload: dict[str, Any]
) -> dict[str, Any]:
    """Change a member's role, never leaving the Board without an Admin."""
    _lock_board(board_id)
    membership = _get_membership(board_id, user_id)
    new_role: str = payload["role"]
    if membership.role == "admin" and new_role != "admin" and _admin_count(board_id) <= 1:
        raise ValidationError("The Board must retain at least one Admin", field="role")
    membership.role = new_role
    display_name = membership.user.display_name
    db.session.commit()
    return _member_to_dict(membership, display_name)


def remove_member_service(board_id: UUID, user_id: UUID, actor: User) -> None:
    """Remove a member, never leaving the Board without an Admin."""
    _lock_board(board_id)
    membership = _get_membership(board_id, user_id)
    if membership.role == "admin" and _admin_count(board_id) <= 1:
        raise ValidationError("The Board must retain at least one Admin")
    db.session.delete(membership)
    record_activity(board_id, actor.id, "member_removed", user_id)
    db.session.commit()


def _link_to_dict(link: InvitationLink) -> dict[str, Any]:
    return {
        "id": link.id,
        "board_id": link.board_id,
        "token": link.token,
        "status": link.status,
        "created_at": link.created_at,
    }


def generate_invitation_service(board_id: UUID, actor: User) -> dict[str, Any]:
    """Create an active Invitation_Link bound to exactly this Board."""
    link = InvitationLink(
        board_id=board_id,
        token=secrets.token_urlsafe(32),
        status="active",
        created_by_id=actor.id,
    )
    db.session.add(link)
    db.session.commit()
    return _link_to_dict(link)


def list_invitations_service(board_id: UUID) -> dict[str, Any]:
    """All Invitation_Links of a Board, newest first."""
    links = db.session.scalars(
        select(InvitationLink)
        .where(InvitationLink.board_id == board_id)
        .order_by(InvitationLink.created_at.desc(), InvitationLink.id.desc())
    ).all()
    return {"items": [_link_to_dict(link) for link in links]}


def revoke_invitation_service(token: str, actor: User) -> dict[str, Any]:
    """Set only this link inactive; the actor must be Admin of the link's Board."""
    link = db.session.scalar(select(InvitationLink).where(InvitationLink.token == token))
    if link is None:
        raise NotFoundError("Invitation link not found")
    if not role_allows(get_board_role(link.board_id, actor.id), "board_admin"):
        raise AuthorizationError("You do not have permission to perform this action")
    link.status = "inactive"
    db.session.commit()
    return _link_to_dict(link)

"""Access_Control_Service: Board member and Invitation_Link management."""

import secrets
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from flask_app.access.rbac import get_board_role, role_allows
from flask_app.activity.service import record_activity
from flask_app.comments.service import list_comments_service
from flask_app.common.exceptions import AuthorizationError, NotFoundError, ValidationError
from flask_app.extensions import db
from flask_app.models import Board, BoardMembership, Card, InvitationLink, TeamMembership, User


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
    record_activity(
        board_id, actor.id, "member_joined", user_id, details={"member_name": user.display_name}
    )
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
    """Remove a Board member whose role is Member; an Admin cannot be removed (R10.10)."""
    _lock_board(board_id)
    membership = _get_membership(board_id, user_id)
    if membership.role == "admin":
        raise ValidationError("An Admin cannot be removed; change the role to Member first")
    member_name = membership.user.display_name
    db.session.delete(membership)
    record_activity(
        board_id, actor.id, "member_removed", user_id, details={"member_name": member_name}
    )
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


def resolve_guest_board(token: str) -> Board:
    """Resolve an Invitation_Link token to its Board, or raise AuthorizationError."""
    link = db.session.scalar(
        select(InvitationLink)
        .options(joinedload(InvitationLink.board))  # type: ignore[arg-type]
        .where(InvitationLink.token == token)
    )
    if link is None or link.status != "active" or link.board.status != "active":
        raise AuthorizationError("This invitation link is not valid")
    board: Board = link.board
    return board


def _guest_user(user: User | None) -> dict[str, Any] | None:
    return None if user is None else {"id": user.id, "display_name": user.display_name}


def guest_board_service(token: str) -> dict[str, Any]:
    """Read-only Board view for a Guest: Columns and Cards, no emails, versions or Activity."""
    board = resolve_guest_board(token)
    cards = db.session.scalars(
        select(Card)
        .options(joinedload(Card.assignee))  # type: ignore[arg-type]
        .where(Card.board_id == board.id)
        .order_by(Card.order_index, Card.id)
    ).all()
    by_column: dict[UUID, list[dict[str, Any]]] = {}
    for card in cards:
        by_column.setdefault(card.column_id, []).append(
            {
                "id": card.id,
                "column_id": card.column_id,
                "title": card.title,
                "description": card.description,
                "assignee": _guest_user(card.assignee),  # type: ignore[arg-type]
                "due_date": card.due_date,
                "order_index": card.order_index,
                "created_at": card.created_at,
                "updated_at": card.updated_at,
                "checklist_items": [
                    {"id": item.id, "text": item.text, "is_done": item.is_done}
                    for item in card.checklist_items  # type: ignore[attr-defined]
                ],
            }
        )
    return {
        "id": board.id,
        "name": board.name,
        "description": board.description,
        "current_user_role": "guest",
        "columns": [
            {
                "id": column.id,
                "name": column.name,
                "order_index": column.order_index,
                "cards": by_column.get(column.id, []),
            }
            for column in board.columns  # type: ignore[attr-defined]
        ],
    }


def guest_comments_service(token: str, card_id: UUID) -> dict[str, Any]:
    """Flat Comment list of a Card on the token's Board, without `version`."""
    board = resolve_guest_board(token)
    card = db.session.get(Card, card_id)
    if card is None or card.board_id != board.id:
        raise NotFoundError("Card not found")
    items = list_comments_service(card_id)["items"]
    return {"items": [{k: v for k, v in item.items() if k != "version"} for item in items]}


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

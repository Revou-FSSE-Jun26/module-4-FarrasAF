from typing import Any
from uuid import UUID

from sqlalchemy import select

from flask_app.access.rbac import get_board_role
from flask_app.common.exceptions import AuthorizationError, NotFoundError, ValidationError
from flask_app.extensions import db
from flask_app.models import Board, BoardMembership, Column, TeamMembership, User

ADMIN = "admin"
DEFAULT_COLUMNS = ("To Do", "Doing", "Done")
_UPDATABLE_FIELDS = ("name", "description", "visibility")


def _board_dict(board: Board, role: str | None) -> dict[str, Any]:
    return {
        "id": board.id,
        "team_id": board.team_id,
        "name": board.name,
        "description": board.description,
        "visibility": board.visibility,
        "status": board.status,
        "current_user_role": role,
        "created_at": board.created_at,
        "updated_at": board.updated_at,
    }


def _get_board(board_id: UUID) -> Board:
    board = db.session.get(Board, board_id)
    if board is None:
        raise NotFoundError("Board not found")
    return board


def create_board_service(payload: dict[str, Any], user: User) -> dict[str, Any]:
    is_team_member = db.session.scalar(
        select(TeamMembership.id).where(
            TeamMembership.team_id == payload["team_id"], TeamMembership.user_id == user.id
        )
    )
    if is_team_member is None:
        raise AuthorizationError("You are not a member of this team")
    board = Board(team_id=payload["team_id"], name=payload["name"])
    db.session.add(board)
    db.session.flush()
    db.session.add(BoardMembership(board_id=board.id, user_id=user.id, role=ADMIN))
    for index, name in enumerate(DEFAULT_COLUMNS):
        db.session.add(Column(board_id=board.id, name=name, order_index=index))
    db.session.commit()
    return _board_dict(board, ADMIN)


def list_boards_service(payload: dict[str, Any], user: User) -> dict[str, Any]:
    archived: bool = payload.get("archived", False)
    query = (
        select(Board, BoardMembership.role)
        .join(BoardMembership, BoardMembership.board_id == Board.id)
        .where(BoardMembership.user_id == user.id)
        .order_by(Board.created_at, Board.id)
    )
    if archived:
        query = query.where(Board.status == "archived", BoardMembership.role == ADMIN)
    else:
        query = query.where(Board.status == "active")
    rows = db.session.execute(query).all()
    return {"items": [_board_dict(board, role) for board, role in rows]}


def get_board_service(board_id: UUID, user: User) -> dict[str, Any]:
    board = _get_board(board_id)
    return _board_dict(board, get_board_role(board_id, user.id))


def update_board_service(board_id: UUID, payload: dict[str, Any], user: User) -> dict[str, Any]:
    board = _get_board(board_id)
    for field in _UPDATABLE_FIELDS:
        if field in payload:
            setattr(board, field, payload[field])
    db.session.commit()
    return _board_dict(board, get_board_role(board_id, user.id))


def archive_board_service(board_id: UUID, user: User) -> dict[str, Any]:
    board = _get_board(board_id)
    board.status = "archived"
    db.session.commit()
    return _board_dict(board, get_board_role(board_id, user.id))


def restore_board_service(board_id: UUID, user: User) -> dict[str, Any]:
    board = _get_board(board_id)
    if board.status != "archived":
        raise ValidationError("Board is not archived")
    board.status = "active"
    db.session.commit()
    return _board_dict(board, get_board_role(board_id, user.id))


def delete_board_service(board_id: UUID) -> None:
    db.session.delete(_get_board(board_id))
    db.session.commit()

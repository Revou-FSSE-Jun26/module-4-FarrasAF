from uuid import UUID

from flask import Blueprint, Response

from flask_app.access.rbac import require_role
from flask_app.auth import current_user, token_required
from flask_app.boards.schema import CreateBoardSchema, ListBoardsQuerySchema, UpdateBoardSchema
from flask_app.boards.service import (
    archive_board_service,
    create_board_service,
    delete_board_service,
    get_board_service,
    list_boards_service,
    restore_board_service,
    update_board_service,
)
from flask_app.common.serialization import json_response, read_json, read_query
from flask_app.common.validation import load_schema

boards_bp = Blueprint("boards", __name__)


@boards_bp.post("/api/boards")
@token_required
def create_board() -> Response:
    payload = load_schema(CreateBoardSchema(), read_json())
    return json_response(create_board_service(payload, current_user()), 201)


@boards_bp.get("/api/boards")
@token_required
def list_boards() -> Response:
    payload = load_schema(ListBoardsQuerySchema(), read_query())
    return json_response(list_boards_service(payload, current_user()))


@boards_bp.get("/api/boards/<uuid:board_id>")
@require_role("member")
def get_board(board_id: UUID) -> Response:
    return json_response(get_board_service(board_id, current_user()))


@boards_bp.patch("/api/boards/<uuid:board_id>")
@require_role("admin")
def update_board(board_id: UUID) -> Response:
    payload = load_schema(UpdateBoardSchema(), read_json())
    return json_response(update_board_service(board_id, payload, current_user()))


@boards_bp.post("/api/boards/<uuid:board_id>/archive")
@require_role("admin")
def archive_board(board_id: UUID) -> Response:
    return json_response(archive_board_service(board_id, current_user()))


@boards_bp.post("/api/boards/<uuid:board_id>/restore")
@require_role("admin")
def restore_board(board_id: UUID) -> Response:
    return json_response(restore_board_service(board_id, current_user()))


@boards_bp.delete("/api/boards/<uuid:board_id>")
@require_role("admin")
def delete_board(board_id: UUID) -> Response:
    delete_board_service(board_id)
    return json_response(status=204)

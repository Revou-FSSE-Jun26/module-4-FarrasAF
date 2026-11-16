from uuid import UUID

from flask import Blueprint, Response

from flask_app.access.rbac import require_role
from flask_app.auth import current_user
from flask_app.columns.schema import CreateColumnSchema, RenameColumnSchema, ReorderColumnSchema
from flask_app.columns.service import (
    create_column_service,
    delete_column_service,
    rename_column_service,
    reorder_column_service,
)
from flask_app.common.serialization import json_response, read_json
from flask_app.common.validation import load_schema

columns_bp = Blueprint("columns", __name__)


@columns_bp.post("/api/boards/<uuid:board_id>/columns")
@require_role("admin")
def create_column(board_id: UUID) -> Response:
    payload = load_schema(CreateColumnSchema(), read_json())
    return json_response(create_column_service(board_id, payload, current_user()), 201)


@columns_bp.patch("/api/columns/<uuid:column_id>")
@require_role("admin")
def rename_column(column_id: UUID) -> Response:
    payload = load_schema(RenameColumnSchema(), read_json())
    return json_response(rename_column_service(column_id, payload))


@columns_bp.post("/api/columns/<uuid:column_id>/reorder")
@require_role("admin")
def reorder_column(column_id: UUID) -> Response:
    payload = load_schema(ReorderColumnSchema(), read_json())
    return json_response(reorder_column_service(column_id, payload))


@columns_bp.delete("/api/columns/<uuid:column_id>")
@require_role("admin")
def delete_column(column_id: UUID) -> Response:
    delete_column_service(column_id, current_user())
    return json_response(status=204)

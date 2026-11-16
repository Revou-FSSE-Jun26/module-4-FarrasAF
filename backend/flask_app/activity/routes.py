from uuid import UUID

from flask import Blueprint, Response

from flask_app.access.rbac import require_role
from flask_app.activity.schema import ActivityQuerySchema
from flask_app.activity.service import list_activity_service
from flask_app.common.serialization import json_response, read_query
from flask_app.common.validation import load_schema

activity_bp = Blueprint("activity", __name__)


@activity_bp.get("/api/boards/<uuid:board_id>/activity")
@require_role("member")
def list_activity(board_id: UUID) -> Response:
    payload = load_schema(ActivityQuerySchema(), read_query())
    return json_response(list_activity_service(board_id, payload))

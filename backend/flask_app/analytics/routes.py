from uuid import UUID

from flask import Blueprint, Response

from flask_app.access.rbac import require_role
from flask_app.analytics.service import get_analytics_service
from flask_app.common.serialization import json_response

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.get("/api/boards/<uuid:board_id>/analytics")
@require_role("member")
def get_analytics(board_id: UUID) -> Response:
    return json_response(get_analytics_service(board_id))

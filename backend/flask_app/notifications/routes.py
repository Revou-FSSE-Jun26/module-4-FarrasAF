from uuid import UUID

from flask import Blueprint, Response

from flask_app.auth import current_user, token_required
from flask_app.common.serialization import json_response, read_query
from flask_app.common.validation import load_schema
from flask_app.notifications.schema import NotificationsQuerySchema
from flask_app.notifications.service import (
    list_notifications_service,
    mark_notification_read_service,
)

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.get("/api/notifications")
@token_required
def list_notifications() -> Response:
    payload = load_schema(NotificationsQuerySchema(), read_query())
    return json_response(list_notifications_service(current_user(), payload))


@notifications_bp.post("/api/notifications/<uuid:notification_id>/read")
@token_required
def mark_notification_read(notification_id: UUID) -> Response:
    return json_response(mark_notification_read_service(notification_id, current_user()))

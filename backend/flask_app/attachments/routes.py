from uuid import UUID

from flask import Blueprint, Response

from flask_app.access.rbac import require_role
from flask_app.attachments.service import (
    MAX_ATTACHMENT_BYTES,
    delete_attachment_service,
    upload_attachment_service,
)
from flask_app.auth import current_user
from flask_app.common.serialization import json_response, read_multipart_file

attachments_bp = Blueprint("attachments", __name__)


@attachments_bp.post("/api/cards/<uuid:card_id>/attachments")
@require_role("member")
def upload_attachment(card_id: UUID) -> Response:
    uploaded = read_multipart_file(MAX_ATTACHMENT_BYTES)
    return json_response(upload_attachment_service(card_id, uploaded, current_user()), 201)


@attachments_bp.delete("/api/attachments/<uuid:attachment_id>")
@require_role("member")
def delete_attachment(attachment_id: UUID) -> Response:
    delete_attachment_service(attachment_id, current_user())
    return json_response(status=204)

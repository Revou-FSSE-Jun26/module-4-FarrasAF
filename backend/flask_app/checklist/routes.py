from uuid import UUID

from flask import Blueprint, Response

from flask_app.access.rbac import require_role
from flask_app.checklist.schema import CreateChecklistItemSchema, UpdateChecklistItemSchema
from flask_app.checklist.service import (
    create_checklist_item_service,
    delete_checklist_item_service,
    update_checklist_item_service,
)
from flask_app.common.serialization import json_response, read_json
from flask_app.common.validation import load_schema

checklist_bp = Blueprint("checklist", __name__)


@checklist_bp.post("/api/cards/<uuid:card_id>/checklist-items")
@require_role("member")
def create_checklist_item(card_id: UUID) -> Response:
    payload = load_schema(CreateChecklistItemSchema(), read_json())
    return json_response(create_checklist_item_service(card_id, payload), 201)


@checklist_bp.patch("/api/checklist-items/<uuid:item_id>")
@require_role("member")
def update_checklist_item(item_id: UUID) -> Response:
    payload = load_schema(UpdateChecklistItemSchema(), read_json())
    return json_response(update_checklist_item_service(item_id, payload))


@checklist_bp.delete("/api/checklist-items/<uuid:item_id>")
@require_role("member")
def delete_checklist_item(item_id: UUID) -> Response:
    delete_checklist_item_service(item_id)
    return json_response(status=204)

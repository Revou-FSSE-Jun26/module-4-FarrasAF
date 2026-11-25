from uuid import UUID

from flask import Blueprint, Response

from flask_app.access.rbac import require_role
from flask_app.auth import current_user
from flask_app.cards.schema import CreateCardSchema, MoveCardSchema, UpdateCardSchema
from flask_app.cards.service import (
    create_card_service,
    delete_card_service,
    get_card_service,
    move_card_service,
    update_card_service,
)
from flask_app.common.serialization import json_response, read_json
from flask_app.common.validation import load_schema

cards_bp = Blueprint("cards", __name__)


@cards_bp.post("/api/columns/<uuid:column_id>/cards")
@require_role("member")
def create_card(column_id: UUID) -> Response:
    payload = load_schema(CreateCardSchema(), read_json())
    return json_response(create_card_service(column_id, payload, current_user()), 201)


@cards_bp.get("/api/cards/<uuid:card_id>")
@require_role("member")
def get_card(card_id: UUID) -> Response:
    return json_response(get_card_service(card_id))


@cards_bp.patch("/api/cards/<uuid:card_id>")
@require_role("member")
def update_card(card_id: UUID) -> Response:
    payload = load_schema(UpdateCardSchema(), read_json())
    return json_response(update_card_service(card_id, payload, current_user()))


@cards_bp.post("/api/cards/<uuid:card_id>/move")
@require_role("member")
def move_card(card_id: UUID) -> Response:
    p = load_schema(MoveCardSchema(), read_json())
    return json_response(
        move_card_service(card_id, p["target_column_id"], p["target_index"], current_user())
    )


@cards_bp.delete("/api/cards/<uuid:card_id>")
@require_role("member")
def delete_card(card_id: UUID) -> Response:
    delete_card_service(card_id, current_user())
    return json_response(status=204)

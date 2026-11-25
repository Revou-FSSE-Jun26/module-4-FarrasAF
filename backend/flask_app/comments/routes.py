from uuid import UUID

from flask import Blueprint, Response

from flask_app.access.rbac import require_role
from flask_app.auth import current_user
from flask_app.comments.schema import CreateCommentSchema, UpdateCommentSchema
from flask_app.comments.service import (
    create_comment_service,
    delete_comment_service,
    list_comments_service,
    update_comment_service,
)
from flask_app.common.serialization import json_response, read_json
from flask_app.common.validation import load_schema

comments_bp = Blueprint("comments", __name__)


@comments_bp.get("/api/cards/<uuid:card_id>/comments")
@require_role("member")
def list_comments(card_id: UUID) -> Response:
    return json_response(list_comments_service(card_id))


@comments_bp.post("/api/cards/<uuid:card_id>/comments")
@require_role("member")
def create_comment(card_id: UUID) -> Response:
    payload = load_schema(CreateCommentSchema(), read_json())
    return json_response(create_comment_service(card_id, payload, current_user()), 201)


@comments_bp.patch("/api/comments/<uuid:comment_id>")
@require_role("member")
def update_comment(comment_id: UUID) -> Response:
    payload = load_schema(UpdateCommentSchema(), read_json())
    return json_response(update_comment_service(comment_id, payload, current_user()))


@comments_bp.delete("/api/comments/<uuid:comment_id>")
@require_role("member")
def delete_comment(comment_id: UUID) -> Response:
    delete_comment_service(comment_id, current_user())
    return json_response(status=204)

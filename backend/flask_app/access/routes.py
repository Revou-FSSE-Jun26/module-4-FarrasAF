from uuid import UUID

from flask import Blueprint, Response

from flask_app.access.rbac import current_user, require_role
from flask_app.access.schema import AddMemberSchema, ChangeMemberRoleSchema
from flask_app.access.service import (
    add_member_service,
    change_member_role_service,
    generate_invitation_service,
    guest_board_service,
    guest_comments_service,
    list_invitations_service,
    list_members_service,
    remove_member_service,
    revoke_invitation_service,
)
from flask_app.auth.decorators import token_required
from flask_app.common.serialization import json_response, read_json
from flask_app.common.validation import load_schema

access_bp = Blueprint("access", __name__)
guest_bp = Blueprint("guest", __name__)


@guest_bp.get("/api/guest/<token>/board")
def guest_board(token: str) -> Response:
    return json_response(guest_board_service(token))


@guest_bp.get("/api/guest/<token>/cards/<uuid:card_id>/comments")
def guest_comments(token: str, card_id: UUID) -> Response:
    return json_response(guest_comments_service(token, card_id))


@access_bp.get("/api/boards/<uuid:board_id>/members")
@require_role("member")
def list_members(board_id: UUID) -> Response:
    return json_response(list_members_service(board_id))


@access_bp.post("/api/boards/<uuid:board_id>/members")
@require_role("admin")
def add_member(board_id: UUID) -> Response:
    payload = load_schema(AddMemberSchema(), read_json())
    return json_response(add_member_service(board_id, payload, current_user()), 201)


@access_bp.patch("/api/boards/<uuid:board_id>/members/<uuid:user_id>")
@require_role("admin")
def change_member_role(board_id: UUID, user_id: UUID) -> Response:
    payload = load_schema(ChangeMemberRoleSchema(), read_json())
    return json_response(change_member_role_service(board_id, user_id, payload))


@access_bp.delete("/api/boards/<uuid:board_id>/members/<uuid:user_id>")
@require_role("admin")
def remove_member(board_id: UUID, user_id: UUID) -> Response:
    remove_member_service(board_id, user_id, current_user())
    return Response(status=204)


@access_bp.get("/api/boards/<uuid:board_id>/invitations")
@require_role("admin")
def list_invitations(board_id: UUID) -> Response:
    return json_response(list_invitations_service(board_id))


@access_bp.post("/api/boards/<uuid:board_id>/invitations")
@require_role("admin")
def generate_invitation(board_id: UUID) -> Response:
    return json_response(generate_invitation_service(board_id, current_user()), 201)


@access_bp.post("/api/invitations/<token>/revoke")
@token_required
def revoke_invitation(token: str) -> Response:
    # No Board id in the path: the service resolves it from the token and checks Admin.
    return json_response(revoke_invitation_service(token, current_user()))

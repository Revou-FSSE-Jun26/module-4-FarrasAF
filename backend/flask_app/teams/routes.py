from uuid import UUID

from flask import Blueprint, Response

from flask_app.auth import current_user, token_required
from flask_app.common.serialization import json_response, read_json
from flask_app.common.validation import load_schema
from flask_app.teams.schema import CreateTeamSchema
from flask_app.teams.service import (
    accept_join_link_service,
    create_team_service,
    generate_join_link_service,
    list_join_links_service,
    list_members_service,
    list_teams_service,
    preview_join_link_service,
    revoke_join_link_service,
)

teams_bp = Blueprint("teams", __name__)


@teams_bp.post("/api/teams")
@token_required
def create_team() -> Response:
    payload = load_schema(CreateTeamSchema(), read_json())
    return json_response(create_team_service(payload, current_user()), 201)


@teams_bp.get("/api/teams")
@token_required
def list_teams() -> Response:
    return json_response(list_teams_service(current_user()))


@teams_bp.get("/api/teams/<uuid:team_id>/members")
@token_required
def list_members(team_id: UUID) -> Response:
    return json_response(list_members_service(team_id, current_user()))


@teams_bp.post("/api/teams/<uuid:team_id>/join-links")
@token_required
def generate_join_link(team_id: UUID) -> Response:
    return json_response(generate_join_link_service(team_id, current_user()), 201)


@teams_bp.get("/api/teams/<uuid:team_id>/join-links")
@token_required
def list_join_links(team_id: UUID) -> Response:
    return json_response(list_join_links_service(team_id, current_user()))


@teams_bp.post("/api/team-join-links/<token>/revoke")
@token_required
def revoke_join_link(token: str) -> Response:
    return json_response(revoke_join_link_service(token, current_user()))


@teams_bp.get("/api/team-join-links/<token>")
@token_required
def preview_join_link(token: str) -> Response:
    return json_response(preview_join_link_service(token))


@teams_bp.post("/api/team-join-links/<token>/accept")
@token_required
def accept_join_link(token: str) -> Response:
    return json_response(accept_join_link_service(token, current_user()))

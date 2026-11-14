from flask import Blueprint, Response, current_app, request

from flask_app.auth.cookies import clear_auth_cookies, set_access_cookie, set_auth_cookies
from flask_app.auth.decorators import current_user, token_required
from flask_app.auth.schema import LoginSchema, RegisterSchema
from flask_app.auth.service import (
    login_service,
    logout_service,
    me_service,
    refresh_service,
    register_service,
)
from flask_app.common.serialization import json_response, read_json
from flask_app.common.validation import load_schema

auth_bp = Blueprint("auth", __name__)


def _refresh_cookie() -> str | None:
    return request.cookies.get(current_app.config["REFRESH_COOKIE_NAME"])


@auth_bp.post("/api/auth/register")
def register() -> Response:
    payload = load_schema(RegisterSchema(), read_json())
    return json_response(register_service(payload), 201)


@auth_bp.post("/api/auth/login")
def login() -> Response:
    identity, access, refresh = login_service(load_schema(LoginSchema(), read_json()))
    response = json_response(identity)
    set_auth_cookies(response, access, refresh)
    return response


@auth_bp.post("/api/auth/refresh")
def refresh() -> Response:
    identity, access = refresh_service(_refresh_cookie())
    response = json_response(identity)
    set_access_cookie(response, access)
    return response


@auth_bp.post("/api/auth/logout")
def logout() -> Response:
    logout_service(_refresh_cookie())
    response = json_response(status=204)
    clear_auth_cookies(response)
    return response


@auth_bp.get("/api/auth/me")
@token_required
def me() -> Response:
    return json_response(me_service(current_user()))

from typing import Any

from flask import Flask, Response, request
from werkzeug.exceptions import HTTPException

from flask_app.auth import auth_bp
from flask_app.common.exceptions import (
    INTERNAL_ERROR,
    AppError,
    AuthorizationError,
)
from flask_app.common.health import health_bp
from flask_app.common.serialization import json_response, to_camel
from flask_app.config import load_config
from flask_app.extensions import db, migrate
from flask_app.teams import teams_bp


def _error_response(status: int, code: str, message: str, field: str | None = None) -> Response:
    error: dict[str, Any] = {"code": code, "message": message}
    if field:
        error["field"] = to_camel(field)
    return json_response({"error": error}, status)


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def handle_app_error(exc: AppError) -> Response:
        db.session.rollback()
        return _error_response(exc.status_code, exc.code, exc.message, exc.field)

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException) -> Response:
        db.session.rollback()
        if request.path.startswith("/api/guest/") and request.method != "GET":
            forbidden = AuthorizationError("Guests have read-only access")
            return _error_response(forbidden.status_code, forbidden.code, forbidden.message)
        code = (exc.name or "error").lower().replace(" ", "_")
        return _error_response(exc.code or 500, code, exc.description or exc.name)

    @app.errorhandler(Exception)
    def handle_unexpected(exc: Exception) -> Response:
        db.session.rollback()
        app.logger.error("Unhandled exception", exc_info=exc)
        return _error_response(500, INTERNAL_ERROR, "Internal server error")


def create_app(config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(config if config is not None else load_config())
    db.init_app(app)
    migrate.init_app(app, db)
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(teams_bp)
    _register_error_handlers(app)
    return app

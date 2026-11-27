from typing import Any

from flask import Flask, Response, g, request
from werkzeug.exceptions import HTTPException

from flask_app.access import access_bp, guest_bp
from flask_app.activity import activity_bp
from flask_app.analytics import analytics_bp
from flask_app.attachments import attachments_bp
from flask_app.auth import auth_bp
from flask_app.boards import boards_bp
from flask_app.cards import cards_bp
from flask_app.checklist import checklist_bp
from flask_app.columns import columns_bp
from flask_app.comments import comments_bp
from flask_app.common.docs import docs_bp
from flask_app.common.exceptions import (
    INTERNAL_ERROR,
    AppError,
    AuthorizationError,
)
from flask_app.common.health import health_bp
from flask_app.common.serialization import json_response, to_camel
from flask_app.config import load_config
from flask_app.extensions import db, migrate
from flask_app.notifications import notifications_bp
from flask_app.search import search_bp
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


def _register_request_logging(app: Flask) -> None:
    @app.after_request
    def log_request(response: Response) -> Response:
        # Route template only: the raw path and query can carry tokens.
        rule = request.url_rule.rule if request.url_rule is not None else "unmatched"
        user = g.get("current_user")
        user_id = user.id if user is not None else "-"
        app.logger.info("%s %s -> %s user=%s", request.method, rule, response.status_code, user_id)
        return response


def create_app(config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(config if config is not None else load_config())
    db.init_app(app)
    migrate.init_app(app, db)
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(teams_bp)
    app.register_blueprint(boards_bp)
    app.register_blueprint(columns_bp)
    app.register_blueprint(cards_bp)
    app.register_blueprint(checklist_bp)
    app.register_blueprint(attachments_bp)
    app.register_blueprint(comments_bp)
    app.register_blueprint(activity_bp)
    app.register_blueprint(access_bp)
    app.register_blueprint(guest_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(analytics_bp)
    if app.config.get("API_DOCS_ENABLED", False):
        app.register_blueprint(docs_bp)
    _register_error_handlers(app)
    _register_request_logging(app)
    return app

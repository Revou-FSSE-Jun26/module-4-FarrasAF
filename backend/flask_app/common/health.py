from flask import Blueprint, Response

from flask_app.common.serialization import json_response

health_bp = Blueprint("health", __name__)


@health_bp.get("/api/health")
def health() -> Response:
    return json_response({"status": "ok"})

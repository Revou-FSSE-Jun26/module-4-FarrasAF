"""Swagger UI for the OpenAPI spec. Registered only in development (see `create_app`)."""

from pathlib import Path

from flask import Blueprint, Response

docs_bp = Blueprint("docs", __name__)

_SPEC_PATH = Path(__file__).resolve().parents[2] / "openapi.yaml"
_SWAGGER_UI_CDN = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5"

_PAGE = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Task Management API</title>
    <link rel="stylesheet" href="{_SWAGGER_UI_CDN}/swagger-ui.css" />
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="{_SWAGGER_UI_CDN}/swagger-ui-bundle.js"></script>
    <script>
      window.ui = SwaggerUIBundle({{
        url: "/api/docs/openapi.yaml",
        dom_id: "#swagger-ui",
        withCredentials: true,
      }});
    </script>
  </body>
</html>
"""


@docs_bp.get("/api/docs")
def swagger_ui() -> Response:
    return Response(_PAGE, mimetype="text/html")


@docs_bp.get("/api/docs/openapi.yaml")
def openapi_spec() -> Response:
    return Response(_SPEC_PATH.read_text(encoding="utf-8"), mimetype="application/yaml")

"""The only place JSON key naming and value formatting is converted."""

import re
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from flask import Response, jsonify, request

from flask_app.common.exceptions import ValidationError

_CAMEL_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")


def to_camel(name: str) -> str:
    head, *rest = name.split("_")
    return head + "".join(part[:1].upper() + part[1:] for part in rest)


def to_snake(name: str) -> str:
    return _CAMEL_BOUNDARY.sub("_", name).lower()


def _convert_keys(value: Any, convert: Any) -> Any:
    if isinstance(value, dict):
        return {
            (convert(k) if isinstance(k, str) else k): _convert_keys(v, convert)
            for k, v in value.items()
        }
    if isinstance(value, list | tuple):
        return [_convert_keys(v, convert) for v in value]
    return value


def _format_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _format_value(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_format_value(v) for v in value]
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        aware = value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
        return aware.isoformat().replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    return value


def read_json() -> dict[str, Any]:
    """Parse the JSON object body with keys converted to snake_case."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object")
    result: dict[str, Any] = _convert_keys(data, to_snake)
    return result


def read_query() -> dict[str, Any]:
    """Query-string values (first value per key) with keys converted to snake_case."""
    return {to_snake(key): value for key, value in request.args.items()}


def json_response(data: Any = None, status: int = 200) -> Response:
    """Serialize with camelCase keys, UUID strings, and ISO 8601 UTC timestamps (`Z`)."""
    if status == 204:
        return Response(status=204)
    response = jsonify(_format_value(_convert_keys(data, to_camel)))
    response.status_code = status
    return response

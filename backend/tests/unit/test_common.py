"""Unit tests for common helpers (Requirements 6.10, 14.2)."""

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest
from flask import Flask
from marshmallow import fields, validate

from flask_app.app import create_app
from flask_app.common.exceptions import (
    AppError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from flask_app.common.ordering import reindex
from flask_app.common.serialization import (
    json_response,
    read_json,
    read_query,
    to_camel,
    to_snake,
)
from flask_app.common.validation import BaseSchema, NonBlankStr, TrimmedStr, load_schema


@pytest.fixture
def app() -> Flask:
    flask_app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite://", "TESTING": False})

    @flask_app.get("/api/_raise_app_error/<kind>")
    def raise_app_error(kind: str) -> str:
        errors: dict[str, AppError] = {
            "validation": ValidationError("bad title", field="due_date"),
            "authn": AuthenticationError("login required"),
            "authz": AuthorizationError("nope"),
            "notfound": NotFoundError("Card not found"),
            "conflict": ConflictError("stale"),
        }
        raise errors[kind]

    @flask_app.get("/api/_boom")
    def boom() -> str:
        raise RuntimeError("secret SQL details")

    return flask_app


# --- serialization -------------------------------------------------------


def test_to_camel_and_to_snake() -> None:
    assert to_camel("order_index") == "orderIndex"
    assert to_camel("title") == "title"
    assert to_snake("orderIndex") == "order_index"
    assert to_snake("parentCommentId") == "parent_comment_id"
    assert to_snake("title") == "title"


def test_read_json_converts_keys_to_snake_case(app: Flask) -> None:
    with app.test_request_context(
        "/x", method="POST", json={"targetIndex": 1, "nested": {"dueDate": None}}
    ):
        assert read_json() == {"target_index": 1, "nested": {"due_date": None}}


def test_read_json_rejects_non_object(app: Flask) -> None:
    with app.test_request_context("/x", method="POST", json=[1, 2]):
        with pytest.raises(ValidationError) as exc:
            read_json()
    assert exc.value.field is None


def test_read_query_converts_keys(app: Flask) -> None:
    with app.test_request_context("/x?pageIndex=2&q=a"):
        assert read_query() == {"page_index": "2", "q": "a"}


def test_json_response_camel_case_and_formats(app: Flask) -> None:
    uid = UUID("12345678-1234-5678-1234-567812345678")
    stamp = datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC)
    with app.test_request_context():
        response = json_response(
            {"card_id": uid, "created_at": stamp, "items": [{"order_index": 0}]}
        )
        assert response.status_code == 200
        assert json.loads(response.get_data()) == {
            "cardId": str(uid),
            "createdAt": "2024-01-02T03:04:05Z",
            "items": [{"orderIndex": 0}],
        }
        empty = json_response(None, 204)
        assert empty.status_code == 204
        assert empty.get_data() == b""


# --- validation ----------------------------------------------------------


class _Schema(BaseSchema):
    title = TrimmedStr(required=True, validate=validate.Length(min=1, max=5))
    body = NonBlankStr()
    version = fields.Int(strict=True)


def test_trimmed_str_trims_before_length_check() -> None:
    assert load_schema(_Schema(), {"title": "  abcde  "}) == {"title": "abcde"}


def test_trimmed_str_blank_fails_min_length() -> None:
    with pytest.raises(ValidationError) as exc:
        load_schema(_Schema(), {"title": "   "})
    assert exc.value.field == "title"


def test_non_blank_str_keeps_value_unchanged_and_rejects_blank() -> None:
    assert load_schema(_Schema(), {"title": "a", "body": "  hi  "})["body"] == "  hi  "
    with pytest.raises(ValidationError) as exc:
        load_schema(_Schema(), {"title": "a", "body": " \n\t"})
    assert exc.value.field == "body"


def test_load_schema_rejects_unknown_and_reports_first_field() -> None:
    with pytest.raises(ValidationError) as exc:
        load_schema(_Schema(), {"title": "a", "extra": 1})
    assert exc.value.field == "extra"
    with pytest.raises(ValidationError) as exc2:
        load_schema(_Schema(), {"title": "a", "version": "1"})
    assert exc2.value.field == "version"


def test_load_schema_non_object_has_no_field() -> None:
    with pytest.raises(ValidationError) as exc:
        load_schema(_Schema(), [1])
    assert exc.value.field is None


# --- error envelope ------------------------------------------------------


@pytest.mark.parametrize(
    ("kind", "status", "code"),
    [
        ("validation", 400, "validation_error"),
        ("authn", 401, "authentication_error"),
        ("authz", 403, "authorization_error"),
        ("notfound", 404, "not_found"),
        ("conflict", 409, "conflict"),
    ],
)
def test_app_errors_map_to_envelope(app: Flask, kind: str, status: int, code: str) -> None:
    response = app.test_client().get(f"/api/_raise_app_error/{kind}")
    assert response.status_code == status
    error = response.get_json()["error"]
    assert error["code"] == code
    assert isinstance(error["message"], str)
    if kind == "validation":
        assert error["field"] == "dueDate"
    else:
        assert "field" not in error


def test_unknown_route_returns_404_envelope(app: Flask) -> None:
    response = app.test_client().get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "not_found"


def test_wrong_method_returns_405_envelope(app: Flask) -> None:
    response = app.test_client().post("/api/health")
    assert response.status_code == 405
    error = response.get_json()["error"]
    assert error["code"] == "method_not_allowed"
    assert "message" in error


def test_unexpected_exception_returns_generic_500(app: Flask) -> None:
    response = app.test_client().get("/api/_boom")
    assert response.status_code == 500
    assert response.get_json() == {
        "error": {"code": "internal_error", "message": "Internal server error"}
    }


def test_non_get_guest_request_returns_403(app: Flask) -> None:
    response = app.test_client().post("/api/guest/sometoken/board")
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "authorization_error"


# --- ordering ------------------------------------------------------------


@dataclass
class _Item:
    order_index: int


def test_reindex_makes_indexes_contiguous_from_zero() -> None:
    items = [_Item(5), _Item(0), _Item(9), _Item(2)]
    reindex(items)
    assert [i.order_index for i in items] == [0, 1, 2, 3]


def test_reindex_empty_and_already_contiguous() -> None:
    reindex([])
    items = [_Item(0), _Item(1)]
    reindex(items)
    assert [i.order_index for i in items] == [0, 1]


# --- health --------------------------------------------------------------


def test_health_returns_200_without_database(app: Flask) -> None:
    # Point at an unreachable database; health must not touch it.
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg://x:x@127.0.0.1:1/none"
    response = app.test_client().get("/api/health")
    assert response.status_code == 200
    body: Any = response.get_json()
    assert body == {"status": "ok"}

"""Property 22: Authentication gate precedes authorization.

Any request to a protected endpoint without a valid access-token cookie is
answered with 401 ``authentication_error``, never 403, whatever the target.

**Validates: Requirements 12.6, 15.9, 15.10**
"""

import uuid
from datetime import timedelta
from typing import Any

import jwt
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from flask_app.auth.service import create_access_token
from flask_app.common.exceptions import AUTHENTICATION_ERROR
from flask_app.common.time import utc_now

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

_COOKIE_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
cookie_text = st.text(alphabet=_COOKIE_ALPHABET, max_size=300)
secrets_ = st.text(alphabet=_COOKIE_ALPHABET, min_size=32, max_size=64)

# Targets that need only authentication. Role-guarded routes share the same
# gate (backend.md rule 2), so the target must not change the outcome.
PROTECTED = [("GET", "/api/auth/me")]


def _assert_unauthenticated(client: Any, token: str | None) -> None:
    if token is not None:
        client.set_cookie("access_token", token)
    for method, path in PROTECTED:
        response = client.open(path, method=method)
        assert response.status_code == 401
        body = response.get_json()
        assert body["error"]["code"] == AUTHENTICATION_ERROR


def _encode(app: Any, claims: dict[str, Any], key: str | None = None) -> str:
    return jwt.encode(claims, key or app.config["JWT_SECRET_KEY"], algorithm="HS256")


# Feature: task-management-app, Property 22: Authentication gate precedes authorization
@_SETTINGS
@given(token=st.one_of(st.none(), st.just(""), cookie_text))
def test_missing_or_garbage_token_gives_401(app: Any, client: Any, token: str | None) -> None:
    _assert_unauthenticated(app.test_client(), token)


# Feature: task-management-app, Property 22: Authentication gate precedes authorization
@_SETTINGS
@given(age_seconds=st.integers(min_value=1, max_value=365 * 24 * 3600))
def test_expired_token_gives_401(app: Any, client: Any, make_user: Any, age_seconds: int) -> None:
    user = make_user()
    now = utc_now()
    claims = {
        "sub": str(user.id),
        "iat": now - timedelta(seconds=age_seconds + 900),
        "exp": now - timedelta(seconds=age_seconds),
    }
    _assert_unauthenticated(app.test_client(), _encode(app, claims))


# Feature: task-management-app, Property 22: Authentication gate precedes authorization
@_SETTINGS
@given(key=secrets_, use_real_user=st.booleans())
def test_token_signed_with_wrong_key_gives_401(
    app: Any, client: Any, make_user: Any, key: str, use_real_user: bool
) -> None:
    if key == app.config["JWT_SECRET_KEY"]:
        return
    sub = make_user().id if use_real_user else uuid.uuid4()
    now = utc_now()
    claims = {"sub": str(sub), "iat": now, "exp": now + timedelta(minutes=15)}
    _assert_unauthenticated(app.test_client(), _encode(app, claims, key))


# Feature: task-management-app, Property 22: Authentication gate precedes authorization
@_SETTINGS
@given(position=st.integers(min_value=0, max_value=20), replacement=st.sampled_from("abcXYZ019"))
def test_tampered_token_gives_401(
    app: Any, client: Any, make_user: Any, position: int, replacement: str
) -> None:
    token = create_access_token(make_user().id)
    head, _, signature = token.rpartition(".")
    index = position % (len(signature) - 1)  # never the last char (padding bits)
    if signature[index] == replacement:
        return
    tampered = f"{head}.{signature[:index]}{replacement}{signature[index + 1 :]}"
    _assert_unauthenticated(app.test_client(), tampered)


# Feature: task-management-app, Property 22: Authentication gate precedes authorization
@_SETTINGS
@given(
    claims_kind=st.sampled_from(["no_exp", "no_sub", "bad_sub", "unknown_user"]),
)
def test_valid_signature_with_unusable_claims_gives_401(
    app: Any, client: Any, claims_kind: str
) -> None:
    now = utc_now()
    claims: dict[str, Any] = {
        "sub": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=15),
    }
    if claims_kind == "no_exp":
        del claims["exp"]
    elif claims_kind == "no_sub":
        del claims["sub"]
    elif claims_kind == "bad_sub":
        claims["sub"] = "not-a-uuid"
    _assert_unauthenticated(app.test_client(), _encode(app, claims))


# Feature: task-management-app, Property 22: Authentication gate precedes authorization
@_SETTINGS
@given(token=cookie_text)
def test_refresh_cookie_is_not_accepted_as_identity(app: Any, client: Any, token: str) -> None:
    fresh = app.test_client()
    fresh.set_cookie("refresh_token", token)
    _assert_unauthenticated(fresh, None)

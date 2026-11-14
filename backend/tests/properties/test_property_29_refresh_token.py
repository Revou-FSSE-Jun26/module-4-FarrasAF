"""Property 29: Refresh-token exchange and revocation.

**Validates: Requirements 15.8, 15.11, 15.12, 15.13**
"""

import uuid
from typing import Any

import jwt
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from flask_app.auth.service import (
    login_service,
    logout_service,
    refresh_service,
    register_service,
)
from flask_app.common.exceptions import AuthenticationError
from tests.conftest import FakeClock

passwords = st.text(
    alphabet=st.characters(blacklist_categories=["Cs", "Cc"]),
    min_size=8,
    max_size=40,
)
local_parts = st.from_regex(r"[a-z][a-z0-9]{2,15}", fullmatch=True)
unknown_tokens = st.one_of(
    st.none(),
    st.just(""),
    st.text(max_size=80),
    st.binary(min_size=1, max_size=48).map(lambda b: b.hex()),
)


def _claims(app: Any, token: str) -> dict[str, Any]:
    # The clock is frozen in the past, so expiry is not checked here.
    claims: dict[str, Any] = jwt.decode(
        token,
        app.config["JWT_SECRET_KEY"],
        algorithms=["HS256"],
        options={"verify_exp": False},
    )
    return claims


def _login(local: str, password: str) -> tuple[str, str, uuid.UUID]:
    email = f"{local}-{uuid.uuid4().hex[:8]}@example.com"
    identity = register_service({"email": email, "password": password, "display_name": "Prop"})
    _, _, refresh = login_service({"email": email, "password": password})
    return email, refresh, identity["id"]


_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)


# Feature: task-management-app, Property 29: Refresh-token exchange and revocation
@_SETTINGS
@given(
    local=local_parts,
    password=passwords,
    elapsed_seconds=st.integers(min_value=0, max_value=7 * 24 * 3600 - 1),
)
def test_valid_refresh_token_yields_identity_only_access_token(
    app: Any, db_session: Any, clock: FakeClock, local: str, password: str, elapsed_seconds: int
) -> None:
    email, refresh, user_id = _login(local, password)
    clock.advance(seconds=elapsed_seconds)

    identity, access = refresh_service(refresh)

    assert identity["id"] == user_id
    assert identity["email"] == email
    claims = _claims(app, access)
    assert claims["sub"] == str(user_id)
    assert set(claims) == {"sub", "iat", "exp"}  # identity only, no role claims
    assert refresh_service(refresh)[0]["id"] == user_id  # exchange does not consume it


# Feature: task-management-app, Property 29: Refresh-token exchange and revocation
@_SETTINGS
@given(
    local=local_parts,
    password=passwords,
    extra_seconds=st.integers(min_value=0, max_value=30 * 24 * 3600),
)
def test_expired_refresh_token_is_rejected(
    db_session: Any, clock: FakeClock, local: str, password: str, extra_seconds: int
) -> None:
    _, refresh, _ = _login(local, password)
    clock.advance(days=7, seconds=extra_seconds)

    with pytest.raises(AuthenticationError):
        refresh_service(refresh)


# Feature: task-management-app, Property 29: Refresh-token exchange and revocation
@_SETTINGS
@given(local=local_parts, password=passwords, logouts=st.integers(min_value=1, max_value=3))
def test_logout_revokes_refresh_token(
    db_session: Any, clock: FakeClock, local: str, password: str, logouts: int
) -> None:
    _, refresh, _ = _login(local, password)
    refresh_service(refresh)  # works before logout

    for _ in range(logouts):
        logout_service(refresh)  # repeated logout stays a no-op

    with pytest.raises(AuthenticationError):
        refresh_service(refresh)


# Feature: task-management-app, Property 29: Refresh-token exchange and revocation
@_SETTINGS
@given(local=local_parts, password=passwords, token=unknown_tokens)
def test_unknown_refresh_token_is_rejected(
    db_session: Any, clock: FakeClock, local: str, password: str, token: str | None
) -> None:
    _, refresh, _ = _login(local, password)
    if token == refresh:
        return

    with pytest.raises(AuthenticationError):
        refresh_service(token)
    logout_service(token)  # unknown token logout is a no-op
    refresh_service(refresh)  # and does not affect real tokens

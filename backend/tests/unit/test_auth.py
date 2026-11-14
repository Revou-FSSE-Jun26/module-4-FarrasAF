"""Unit tests for the Authentication_Service (R15.2, R15.4-R15.8, R15.11, R15.15)."""

from datetime import timedelta
from typing import Any

import pytest

from flask_app.auth.service import (
    LOCKOUT_MINUTES,
    MAX_FAILED_LOGINS,
    hash_refresh_token,
    login_service,
    register_service,
)
from flask_app.common.exceptions import AuthenticationError, ValidationError
from flask_app.models import RefreshToken, User

EMAIL = "alice@example.com"
PASSWORD = "correct-horse-battery"
WRONG = "wrong-password-123"


def _register(email: str = EMAIL) -> dict[str, Any]:
    return register_service({"email": email, "password": PASSWORD, "display_name": "Alice"})


def _login(password: str = PASSWORD) -> tuple[dict[str, Any], str, str]:
    return login_service({"email": EMAIL, "password": password})


def _set_cookie_headers(response: Any) -> list[str]:
    return list(response.headers.getlist("Set-Cookie"))


def _cookie_header(response: Any, name: str) -> list[str]:
    return [h for h in _set_cookie_headers(response) if h.startswith(f"{name}=")]


def test_login_sets_both_cookies_and_returns_identity(client: Any, db_session: Any) -> None:
    _register()
    response = client.post("/api/auth/login", json={"email": EMAIL, "password": PASSWORD})

    assert response.status_code == 200
    body = response.get_json()
    assert body["email"] == EMAIL
    assert body["displayName"] == "Alice"
    assert "id" in body
    assert "token" not in str(body).lower()
    assert "password" not in str(body).lower()

    access = _cookie_header(response, "access_token")
    refresh = _cookie_header(response, "refresh_token")
    assert len(access) == 1
    assert len(refresh) >= 1
    for header in access + refresh:
        assert "HttpOnly" in header
        assert "SameSite=Lax" in header
        assert "Domain" not in header
    assert "Path=/;" in access[0] or access[0].endswith("Path=/")
    assert {"Path=/api/auth/refresh" in h or "Path=/api/auth/logout" in h for h in refresh} == {
        True
    }


def test_login_stores_only_hashed_refresh_token(db_session: Any) -> None:
    _register()
    _, _, refresh = _login()

    stored = db_session.query(RefreshToken).all()
    assert len(stored) == 1
    assert stored[0].token_hash == hash_refresh_token(refresh)
    assert stored[0].token_hash != refresh
    assert stored[0].revoked is False


def test_logout_revokes_refresh_token_and_clears_cookies(client: Any, db_session: Any) -> None:
    _register()
    client.post("/api/auth/login", json={"email": EMAIL, "password": PASSWORD})
    cookie = client.get_cookie("refresh_token", path="/api/auth/logout")
    assert cookie is not None

    response = client.post("/api/auth/logout")

    assert response.status_code == 204
    tokens = db_session.query(RefreshToken).all()
    assert len(tokens) == 1
    assert tokens[0].revoked is True
    for name in ("access_token", "refresh_token"):
        headers = _cookie_header(response, name)
        assert headers
        assert all("Expires=Thu, 01 Jan 1970" in h or "Max-Age=0" in h for h in headers)

    # The revoked refresh token can no longer be used.
    client.set_cookie("refresh_token", cookie.value, path="/api/auth/refresh")
    assert client.post("/api/auth/refresh").status_code == 401


def test_logout_without_cookie_is_a_noop(client: Any) -> None:
    assert client.post("/api/auth/logout").status_code == 204


def test_refresh_issues_new_identity_only_access_token(client: Any, db_session: Any) -> None:
    _register()
    client.post("/api/auth/login", json={"email": EMAIL, "password": PASSWORD})

    response = client.post("/api/auth/refresh")

    assert response.status_code == 200
    assert response.get_json()["email"] == EMAIL
    assert len(_cookie_header(response, "access_token")) == 1
    assert _cookie_header(response, "refresh_token") == []
    # The new access cookie authenticates the user.
    assert client.get("/api/auth/me").get_json()["email"] == EMAIL


def test_refresh_without_valid_token_is_rejected(client: Any) -> None:
    response = client.post("/api/auth/refresh")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "authentication_error"


def test_register_duplicate_email_rejected(db_session: Any) -> None:
    _register()
    with pytest.raises(ValidationError) as exc:
        _register("ALICE@example.com ")
    assert exc.value.field == "email"
    assert db_session.query(User).filter(User.email == EMAIL).count() == 1


def test_register_stores_hash_and_returns_identity_only(db_session: Any) -> None:
    identity = _register()
    assert set(identity) == {"id", "email", "display_name"}
    user = db_session.get(User, identity["id"])
    assert user.password_hash != PASSWORD
    assert user.password_hash.startswith("$argon2")


def test_login_unknown_email_and_wrong_password_share_message(db_session: Any) -> None:
    _register()
    with pytest.raises(AuthenticationError) as unknown:
        login_service({"email": "nobody@example.com", "password": WRONG})
    with pytest.raises(AuthenticationError) as wrong:
        _login(WRONG)
    assert str(unknown.value) == str(wrong.value)


def test_three_consecutive_failures_lock_the_account(db_session: Any, clock: Any) -> None:
    _register()
    for _ in range(MAX_FAILED_LOGINS):
        with pytest.raises(AuthenticationError):
            _login(WRONG)

    user = db_session.query(User).filter(User.email == EMAIL).one()
    assert user.failed_login_attempts == MAX_FAILED_LOGINS
    assert user.locked_until == clock.now + timedelta(minutes=LOCKOUT_MINUTES)


def test_locked_login_rejected_even_with_correct_password(db_session: Any, clock: Any) -> None:
    _register()
    for _ in range(MAX_FAILED_LOGINS):
        with pytest.raises(AuthenticationError):
            _login(WRONG)

    with pytest.raises(AuthenticationError) as locked:
        _login(PASSWORD)
    with pytest.raises(AuthenticationError) as wrong:
        _login(WRONG)
    # Lockout is indistinguishable from bad credentials (R15.3, R15.5).
    assert str(locked.value) == str(wrong.value)

    clock.advance(minutes=LOCKOUT_MINUTES - 1, seconds=59)
    with pytest.raises(AuthenticationError):
        _login(PASSWORD)


def test_account_unlocks_after_lockout_window(db_session: Any, clock: Any) -> None:
    _register()
    for _ in range(MAX_FAILED_LOGINS):
        with pytest.raises(AuthenticationError):
            _login(WRONG)

    clock.advance(minutes=LOCKOUT_MINUTES)
    identity, access, refresh = _login(PASSWORD)

    assert identity["email"] == EMAIL
    assert access
    assert refresh
    user = db_session.query(User).filter(User.email == EMAIL).one()
    assert user.failed_login_attempts == 0
    assert user.locked_until is None


def test_successful_login_resets_failure_counter(db_session: Any, clock: Any) -> None:
    _register()
    for _ in range(MAX_FAILED_LOGINS - 1):
        with pytest.raises(AuthenticationError):
            _login(WRONG)
    _login(PASSWORD)
    for _ in range(MAX_FAILED_LOGINS - 1):
        with pytest.raises(AuthenticationError):
            _login(WRONG)

    # Two failures after the reset do not lock the account.
    user = db_session.query(User).filter(User.email == EMAIL).one()
    assert user.locked_until is None
    assert _login(PASSWORD)[0]["email"] == EMAIL

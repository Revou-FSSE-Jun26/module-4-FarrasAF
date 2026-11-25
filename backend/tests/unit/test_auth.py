"""Unit tests for the Authentication_Service (R15.2, R15.4-R15.8, R15.11, R15.15)."""

from datetime import UTC, datetime, timedelta
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


# --- Profile service (R18.2-R18.10) -------------------------------------------------

NEW_PASSWORD = "a-brand-new-password"


def _login_client(client: Any, db_session: Any) -> User:
    _register()
    assert (
        client.post("/api/auth/login", json={"email": EMAIL, "password": PASSWORD}).status_code
        == 200
    )
    user: User = db_session.query(User).filter(User.email == EMAIL).one()
    return user


def _change(client: Any, current: str = PASSWORD, new: str = NEW_PASSWORD) -> Any:
    return client.post(
        "/api/auth/me/password", json={"currentPassword": current, "newPassword": new}
    )


def test_display_name_is_trimmed_and_stored(client: Any, db_session: Any) -> None:
    user = _login_client(client, db_session)

    response = client.patch("/api/auth/me", json={"displayName": "  Alicia  "})

    assert response.status_code == 200
    assert response.get_json()["displayName"] == "Alicia"
    db_session.refresh(user)
    assert user.display_name == "Alicia"
    assert client.get("/api/auth/me").get_json()["displayName"] == "Alicia"


@pytest.mark.parametrize("name", ["", "   ", "x" * 51])
def test_invalid_display_name_rejected(client: Any, db_session: Any, name: str) -> None:
    user = _login_client(client, db_session)

    response = client.patch("/api/auth/me", json={"displayName": name})

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "validation_error"
    db_session.refresh(user)
    assert user.display_name == "Alice"


def test_fifty_character_display_name_accepted(client: Any, db_session: Any) -> None:
    _login_client(client, db_session)
    response = client.patch("/api/auth/me", json={"displayName": "x" * 50})
    assert response.status_code == 200


def test_email_key_rejected_and_email_unchanged(client: Any, db_session: Any) -> None:
    user = _login_client(client, db_session)

    response = client.patch(
        "/api/auth/me", json={"displayName": "Alicia", "email": "other@example.com"}
    )

    assert response.status_code == 400
    db_session.refresh(user)
    assert user.email == EMAIL
    assert user.display_name == "Alice"


def test_rename_appears_in_board_and_team_member_responses(
    client: Any, db_session: Any, make_board: Any
) -> None:
    user = _login_client(client, db_session)
    board = make_board(admin=user)

    assert client.patch("/api/auth/me", json={"displayName": "Renamed"}).status_code == 200

    members = client.get(f"/api/boards/{board.id}/members").get_json()["items"]
    assert [m["displayName"] for m in members] == ["Renamed"]
    team_members = client.get(f"/api/teams/{board.team_id}/members").get_json()["items"]
    assert [m["displayName"] for m in team_members] == ["Renamed"]


def test_password_change_revokes_tokens_issues_cookies_and_resets_failures(
    client: Any, db_session: Any
) -> None:
    user = _login_client(client, db_session)
    old_hash = user.password_hash
    user.failed_login_attempts = MAX_FAILED_LOGINS - 1
    db_session.flush()

    response = _change(client)

    assert response.status_code == 200
    assert len(_cookie_header(response, "access_token")) == 1
    assert len(_cookie_header(response, "refresh_token")) >= 1
    tokens = db_session.query(RefreshToken).all()
    assert len(tokens) == 2
    assert sorted(t.revoked for t in tokens) == [False, True]
    db_session.refresh(user)
    assert user.password_hash != old_hash
    assert user.failed_login_attempts == 0
    assert user.locked_until is None
    # New password works; old one no longer does.
    assert _login(NEW_PASSWORD)[0]["email"] == EMAIL
    with pytest.raises(AuthenticationError):
        _login(PASSWORD)


def test_wrong_current_password_counts_and_third_failure_locks(
    client: Any, db_session: Any, clock: Any
) -> None:
    clock.set(datetime.now(UTC))  # JWT validation uses the real clock
    user = _login_client(client, db_session)

    for expected in range(1, MAX_FAILED_LOGINS):
        response = _change(client, current=WRONG)
        assert response.status_code == 400
        db_session.refresh(user)
        assert user.failed_login_attempts == expected
        assert user.locked_until is None

    assert _change(client, current=WRONG).status_code == 400
    db_session.refresh(user)
    assert user.failed_login_attempts == MAX_FAILED_LOGINS
    assert user.locked_until == clock.now + timedelta(minutes=LOCKOUT_MINUTES)
    with pytest.raises(AuthenticationError):
        _login(PASSWORD)


def test_locked_account_gets_same_error_even_with_correct_password(
    client: Any, db_session: Any, clock: Any
) -> None:
    clock.set(datetime.now(UTC))  # JWT validation uses the real clock
    _login_client(client, db_session)
    wrong_body = _change(client, current=WRONG).get_json()
    _change(client, current=WRONG)
    _change(client, current=WRONG)

    locked = _change(client, current=PASSWORD)

    assert locked.status_code == 400
    assert locked.get_json() == wrong_body
    # The password was not changed.
    clock.advance(minutes=LOCKOUT_MINUTES)
    assert _login(PASSWORD)[0]["email"] == EMAIL


@pytest.mark.parametrize(
    ("new", "current"),
    [("short", PASSWORD), (PASSWORD, PASSWORD)],
)
def test_short_or_unchanged_new_password_not_counted(
    client: Any, db_session: Any, new: str, current: str
) -> None:
    user = _login_client(client, db_session)
    old_hash = user.password_hash

    response = _change(client, current=current, new=new)

    assert response.status_code == 400
    db_session.refresh(user)
    assert user.failed_login_attempts == 0
    assert user.password_hash == old_hash
    assert all(not t.revoked for t in db_session.query(RefreshToken).all())


def test_unauthenticated_profile_requests_get_401(client: Any) -> None:
    assert client.patch("/api/auth/me", json={"displayName": "X"}).status_code == 401
    assert _change(client).status_code == 401

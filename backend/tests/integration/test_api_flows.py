"""End-to-end API flows through the authentication and RBAC gates.

Covers R12.6 (401 before 403), R12.2 (Guest read-only), R12.1 (role read from
storage on every request), R14.5 / R13 (no lost update) and R15.4-R15.5 (lockout).
"""

import uuid
from collections.abc import Callable
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from flask_app.models import Board, BoardMembership, Card, Column, TeamMembership, User

PASSWORD = "correct-horse-battery"

MakeBoard = Callable[..., Board]
MakeColumn = Callable[..., Column]
MakeCard = Callable[..., Card]


def _register(client: FlaskClient, email: str, password: str = PASSWORD) -> None:
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "displayName": "Flow User"},
    )
    assert response.status_code == 201, response.get_json()


def _login(client: FlaskClient, email: str, password: str = PASSWORD) -> Any:
    return client.post("/api/auth/login", json={"email": email, "password": password})


@pytest.fixture
def make_session(app: Flask, db_session: Any) -> Callable[[], tuple[FlaskClient, User]]:
    """Register and log in a fresh User; return its own client (cookie jar) and the model."""

    def _make() -> tuple[FlaskClient, User]:
        client = app.test_client()
        email = f"flow-{uuid.uuid4().hex[:12]}@example.com"
        _register(client, email)
        assert _login(client, email).status_code == 200
        user_id = uuid.UUID(client.get("/api/auth/me").get_json()["id"])
        user = db_session.get(User, user_id)
        assert user is not None
        return client, user

    return _make


def _join(db_session: Any, board: Board, user: User, role: str) -> None:
    db_session.add(TeamMembership(team_id=board.team_id, user_id=user.id, team_role="team_regular"))
    db_session.add(BoardMembership(board_id=board.id, user_id=user.id, role=role))
    db_session.flush()


def test_unauthenticated_gets_401_before_any_role_check(
    client: FlaskClient, make_card: MakeCard
) -> None:
    card = make_card()
    # Role-protected routes: 401 even though the caller has no role on the Board (R12.6).
    assert client.get(f"/api/cards/{card.id}").status_code == 401
    assert client.patch(f"/api/cards/{card.id}", json={"title": "x"}).status_code == 401
    assert (
        client.post(f"/api/boards/{card.board_id}/columns", json={"name": "c"}).status_code == 401
    )
    body = client.get(f"/api/cards/{card.id}").get_json()
    assert body["error"]["code"] == "authentication_error"


def test_authenticated_without_membership_gets_403(
    make_session: Callable[[], tuple[FlaskClient, User]], make_card: MakeCard
) -> None:
    outsider, _ = make_session()
    card = make_card()
    response = outsider.get(f"/api/cards/{card.id}")
    assert response.status_code == 403


def test_guest_link_is_read_only_and_writes_are_rejected(
    db_session: Any,
    client: FlaskClient,
    make_session: Callable[[], tuple[FlaskClient, User]],
    make_board: MakeBoard,
    make_column: MakeColumn,
    make_card: MakeCard,
) -> None:
    admin_client, admin = make_session()
    board = make_board(admin=admin)
    column = make_column(board=board)
    card = make_card(column=column, title="Visible", created_by=admin)

    created = admin_client.post(f"/api/boards/{board.id}/invitations")
    assert created.status_code == 201
    token = created.get_json()["token"]

    # Anonymous Guest can read.
    guest_view = client.get(f"/api/guest/{token}/board")
    assert guest_view.status_code == 200
    assert guest_view.get_json()["currentUserRole"] == "guest"
    assert client.get(f"/api/guest/{token}/cards/{card.id}/comments").status_code == 200

    # Guest write attempts never reach a handler: no cookie means 401, and the
    # guest routes themselves reject any non-GET method with 403.
    assert (
        client.patch(f"/api/cards/{card.id}", json={"title": "Hacked", "version": 1}).status_code
        == 401
    )
    assert client.post(f"/api/guest/{token}/board", json={}).status_code == 403
    assert client.delete(f"/api/guest/{token}/board").status_code == 403

    db_session.refresh(card)
    assert card.title == "Visible"


def test_role_change_applies_on_the_next_request(
    db_session: Any,
    make_session: Callable[[], tuple[FlaskClient, User]],
    make_board: MakeBoard,
    make_column: MakeColumn,
) -> None:
    admin_client, admin = make_session()
    member_client, member = make_session()
    board = make_board(admin=admin)
    make_column(board=board)
    _join(db_session, board, member, "admin")

    # Same access token throughout: only the stored membership changes.
    assert (
        member_client.post(f"/api/boards/{board.id}/columns", json={"name": "A"}).status_code == 201
    )

    demote = admin_client.patch(
        f"/api/boards/{board.id}/members/{member.id}", json={"role": "member"}
    )
    assert demote.status_code == 200
    assert (
        member_client.post(f"/api/boards/{board.id}/columns", json={"name": "B"}).status_code == 403
    )

    promote = admin_client.patch(
        f"/api/boards/{board.id}/members/{member.id}", json={"role": "admin"}
    )
    assert promote.status_code == 200
    assert (
        member_client.post(f"/api/boards/{board.id}/columns", json={"name": "C"}).status_code == 201
    )

    remove = admin_client.delete(f"/api/boards/{board.id}/members/{member.id}")
    assert remove.status_code == 204
    assert member_client.get(f"/api/boards/{board.id}/members").status_code == 403


def test_concurrent_card_edits_lose_no_update(
    db_session: Any,
    make_session: Callable[[], tuple[FlaskClient, User]],
    make_board: MakeBoard,
    make_column: MakeColumn,
    make_card: MakeCard,
) -> None:
    first, user_one = make_session()
    second, user_two = make_session()
    board = make_board(admin=user_one)
    _join(db_session, board, user_two, "member")
    column = make_column(board=board)
    card = make_card(column=column, title="Original", created_by=user_one)

    # Both users load the same version, then both submit an edit (R14.5).
    version = first.get(f"/api/cards/{card.id}").get_json()["version"]
    assert second.get(f"/api/cards/{card.id}").get_json()["version"] == version

    won = first.patch(f"/api/cards/{card.id}", json={"title": "First", "version": version})
    lost = second.patch(f"/api/cards/{card.id}", json={"title": "Second", "version": version})
    assert won.status_code == 200
    assert lost.status_code == 409

    stored = second.get(f"/api/cards/{card.id}").get_json()
    assert stored["title"] == "First"
    assert stored["version"] != version

    # After re-reading, the loser's retry succeeds and neither edit is silently lost.
    retry = second.patch(
        f"/api/cards/{card.id}", json={"title": "Second", "version": stored["version"]}
    )
    assert retry.status_code == 200
    assert first.get(f"/api/cards/{card.id}").get_json()["title"] == "Second"


def test_edits_to_distinct_cards_are_independent(
    db_session: Any,
    make_session: Callable[[], tuple[FlaskClient, User]],
    make_board: MakeBoard,
    make_column: MakeColumn,
    make_card: MakeCard,
) -> None:
    first, user_one = make_session()
    second, user_two = make_session()
    board = make_board(admin=user_one)
    _join(db_session, board, user_two, "member")
    column = make_column(board=board)
    card_a = make_card(column=column, title="A", created_by=user_one)
    card_b = make_card(column=column, title="B", created_by=user_one)

    assert (
        first.patch(f"/api/cards/{card_a.id}", json={"title": "A2", "version": 1}).status_code
        == 200
    )
    assert (
        second.patch(f"/api/cards/{card_b.id}", json={"title": "B2", "version": 1}).status_code
        == 200
    )

    assert first.get(f"/api/cards/{card_a.id}").get_json()["title"] == "A2"
    assert first.get(f"/api/cards/{card_b.id}").get_json()["title"] == "B2"


def test_lockout_after_three_failures_then_expires(app: Flask, db_session: Any, clock: Any) -> None:
    client = app.test_client()
    email = f"lock-{uuid.uuid4().hex[:12]}@example.com"
    _register(client, email)

    wrong = [_login(client, email, "wrong-password-1") for _ in range(3)]
    assert [r.status_code for r in wrong] == [401, 401, 401]

    # Locked: even the correct password is rejected, with the same generic error (R15.5).
    locked = _login(client, email)
    assert locked.status_code == 401
    assert locked.get_json() == wrong[0].get_json()
    assert client.get("/api/auth/me").status_code == 401  # no token was issued
    assert "Set-Cookie" not in locked.headers

    clock.advance(minutes=14, seconds=59)
    assert _login(client, email).status_code == 401

    clock.advance(seconds=2)
    ok = _login(client, email)
    assert ok.status_code == 200
    # Tokens are issued again. (The frozen clock makes the JWT look expired to
    # PyJWT, which uses real time, so /me is not checked here.)
    assert any(c.startswith("access_token=") for c in ok.headers.getlist("Set-Cookie"))


def test_successful_login_resets_failure_count(app: Flask, db_session: Any) -> None:
    client = app.test_client()
    email = f"reset-{uuid.uuid4().hex[:12]}@example.com"
    _register(client, email)

    for _ in range(2):
        assert _login(client, email, "wrong-password-1").status_code == 401
    assert _login(client, email).status_code == 200
    for _ in range(2):
        assert _login(client, email, "wrong-password-1").status_code == 401
    # Two failures after a reset: still not locked.
    assert _login(client, email).status_code == 200

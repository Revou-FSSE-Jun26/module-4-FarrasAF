"""Unit tests for the Guest routes (R11.3, R11.4, R11.6, R11.8)."""

from collections.abc import Callable
from typing import Any

from flask_app.auth.service import create_access_token
from flask_app.models import Board, Card, Comment, InvitationLink, User

TOKEN = "guest-test-token"


def _link(db_session: Any, board: Board, user: User, token: str = TOKEN) -> InvitationLink:
    link = InvitationLink(board_id=board.id, token=token, status="active", created_by_id=user.id)
    db_session.add(link)
    db_session.flush()
    return link


def _error_code(response: Any) -> str:
    code: str = response.get_json()["error"]["code"]
    return code


def _contains_key(value: Any, forbidden: set[str]) -> bool:
    if isinstance(value, dict):
        return any(k in forbidden or _contains_key(v, forbidden) for k, v in value.items())
    if isinstance(value, list):
        return any(_contains_key(v, forbidden) for v in value)
    return False


def test_unknown_token_is_rejected_with_authorization_error(
    db_session: Any, client: Any, make_card: Callable[..., Card]
) -> None:
    card = make_card()
    db_session.commit()
    for url in ("/api/guest/nope/board", f"/api/guest/nope/cards/{card.id}/comments"):
        response = client.get(url)
        assert response.status_code == 403
        assert _error_code(response) == "authorization_error"


def test_guest_rejects_non_get_requests_with_403(
    db_session: Any, client: Any, make_board: Callable[..., Board], make_user: Callable[..., User]
) -> None:
    owner = make_user()
    board = make_board(admin=owner)
    _link(db_session, board, owner)
    db_session.commit()
    for method in ("post", "put", "patch", "delete"):
        response = getattr(client, method)(f"/api/guest/{TOKEN}/board", json={})
        assert response.status_code == 403
        assert _error_code(response) == "authorization_error"


def test_authenticated_user_without_board_role_gets_403(
    db_session: Any, client: Any, make_board: Callable[..., Board], make_user: Callable[..., User]
) -> None:
    board = make_board()
    outsider = make_user()
    db_session.commit()
    client.set_cookie("access_token", create_access_token(outsider.id))
    response = client.get(f"/api/boards/{board.id}/members")
    assert response.status_code == 403
    assert _error_code(response) == "authorization_error"


def test_request_without_cookies_to_authenticated_route_gets_401(
    db_session: Any, client: Any, make_board: Callable[..., Board]
) -> None:
    board = make_board()
    db_session.commit()
    response = client.get(f"/api/boards/{board.id}/members")
    assert response.status_code == 401
    assert _error_code(response) == "authentication_error"


def test_guest_payload_has_no_emails_version_or_activity(
    db_session: Any,
    client: Any,
    make_user: Callable[..., User],
    make_board: Callable[..., Board],
    make_column: Callable[..., Any],
    make_card: Callable[..., Card],
) -> None:
    owner = make_user(display_name="Owner")
    board = make_board(admin=owner)
    column = make_column(board=board)
    card = make_card(column=column, created_by=owner, assignee=owner)
    db_session.add(Comment(card_id=card.id, author_id=owner.id, body="hello", version=1))
    _link(db_session, board, owner)
    db_session.commit()

    response = client.get(f"/api/guest/{TOKEN}/board")
    assert response.status_code == 200
    data = response.get_json()
    assert data["currentUserRole"] == "guest"
    assert data["columns"][0]["cards"][0]["assignee"] == {
        "id": str(owner.id),
        "displayName": "Owner",
    }
    forbidden = {"email", "version", "activity"}
    assert not _contains_key(data, forbidden)
    assert owner.email not in response.get_data(as_text=True)

    comments = client.get(f"/api/guest/{TOKEN}/cards/{card.id}/comments")
    assert comments.status_code == 200
    items = comments.get_json()["items"]
    assert len(items) == 1 and items[0]["body"] == "hello"
    assert not _contains_key(items, forbidden)


def test_archived_board_token_is_rejected(
    db_session: Any, client: Any, make_user: Callable[..., User], make_board: Callable[..., Board]
) -> None:
    owner = make_user()
    board = make_board(admin=owner)
    _link(db_session, board, owner)
    db_session.commit()
    assert client.get(f"/api/guest/{TOKEN}/board").status_code == 200
    board.status = "archived"
    db_session.commit()
    response = client.get(f"/api/guest/{TOKEN}/board")
    assert response.status_code == 403
    assert _error_code(response) == "authorization_error"


def test_card_outside_token_board_returns_not_found(
    db_session: Any,
    client: Any,
    make_user: Callable[..., User],
    make_board: Callable[..., Board],
    make_column: Callable[..., Any],
    make_card: Callable[..., Card],
) -> None:
    owner = make_user()
    board = make_board(admin=owner)
    _link(db_session, board, owner)
    other_card = make_card(column=make_column(board=make_board()))
    db_session.commit()
    response = client.get(f"/api/guest/{TOKEN}/cards/{other_card.id}/comments")
    assert response.status_code == 404
    assert _error_code(response) == "not_found"

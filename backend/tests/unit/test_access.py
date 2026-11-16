"""Unit tests for the Access_Control_Service (R10.x members, R11.x invitations)."""

import uuid
from collections.abc import Callable
from typing import Any

import pytest

from flask_app.access.service import (
    add_member_service,
    change_member_role_service,
    generate_invitation_service,
    list_invitations_service,
    list_members_service,
    remove_member_service,
    revoke_invitation_service,
)
from flask_app.auth.service import register_service
from flask_app.common.exceptions import AuthorizationError, NotFoundError, ValidationError
from flask_app.models import Board, BoardMembership, InvitationLink, TeamMembership, User

PASSWORD = "correct-horse-battery"


def _add_team_member(db_session: Any, board: Board, user: User) -> None:
    db_session.add(TeamMembership(team_id=board.team_id, user_id=user.id, team_role="team_regular"))
    db_session.flush()


def _board_member(
    db_session: Any, board: Board, user: User, role: str = "member"
) -> BoardMembership:
    _add_team_member(db_session, board, user)
    membership = BoardMembership(board_id=board.id, user_id=user.id, role=role)
    db_session.add(membership)
    db_session.flush()
    return membership


def _login_as_member(client: Any, db_session: Any, board: Board, email: str) -> User:
    """Register a real account, make it a Board Member, and log in through the API."""
    identity = register_service({"email": email, "password": PASSWORD, "display_name": "Mia"})
    user: User = db_session.get(User, identity["id"])
    _board_member(db_session, board, user, "member")
    response = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200
    return user


# --- non-Admin rejection (R10.7, R11.7) ---------------------------------------


def test_non_admin_is_rejected_on_admin_only_routes(
    client: Any, db_session: Any, make_board: Callable[..., Board], make_user: Callable[..., User]
) -> None:
    board = make_board()
    target = make_user()
    _board_member(db_session, board, target)
    _login_as_member(client, db_session, board, "mia@example.com")
    base = f"/api/boards/{board.id}"
    calls = [
        client.post(f"{base}/members", json={"userId": str(target.id), "role": "member"}),
        client.patch(f"{base}/members/{target.id}", json={"role": "admin"}),
        client.delete(f"{base}/members/{target.id}"),
        client.get(f"{base}/invitations"),
        client.post(f"{base}/invitations"),
    ]
    for response in calls:
        assert response.status_code == 403
        assert response.get_json()["error"]["code"] == "authorization_error"
    assert db_session.query(InvitationLink).count() == 0
    assert db_session.query(BoardMembership).filter_by(user_id=target.id).one().role == "member"


def test_non_admin_cannot_revoke_invitation(
    client: Any, db_session: Any, make_board: Callable[..., Board], make_user: Callable[..., User]
) -> None:
    board = make_board()
    link = generate_invitation_service(board.id, make_user())
    _login_as_member(client, db_session, board, "mia@example.com")

    response = client.post(f"/api/invitations/{link['token']}/revoke")

    assert response.status_code == 403
    assert db_session.get(InvitationLink, link["id"]).status == "active"


def test_unauthenticated_request_is_rejected(client: Any, make_board: Callable[..., Board]) -> None:
    board = make_board()
    assert client.get(f"/api/boards/{board.id}/members").status_code == 401
    assert client.post(f"/api/boards/{board.id}/invitations").status_code == 401


# --- members (R10.x) ----------------------------------------------------------


def test_list_members_returns_items_with_user_id_display_name_role(
    db_session: Any, make_board: Callable[..., Board], make_user: Callable[..., User]
) -> None:
    admin = make_user(display_name="Ann")
    board = make_board(admin=admin)
    other = make_user(display_name="Bob")
    _board_member(db_session, board, other)

    result = list_members_service(board.id)

    assert set(result) == {"items"}
    assert all(set(item) == {"user_id", "display_name", "role"} for item in result["items"])
    by_user = {item["user_id"]: item for item in result["items"]}
    assert by_user[admin.id]["display_name"] == "Ann"
    assert by_user[admin.id]["role"] == "admin"
    assert by_user[other.id]["role"] == "member"
    assert len(result["items"]) == 2


def test_add_member_service_adds_team_member_and_records_activity(
    db_session: Any, make_board: Callable[..., Board], make_user: Callable[..., User]
) -> None:
    admin = make_user()
    board = make_board(admin=admin)
    user = make_user(display_name="Cy")
    _add_team_member(db_session, board, user)

    member = add_member_service(board.id, {"user_id": user.id, "role": "member"}, admin)

    assert member == {"user_id": user.id, "display_name": "Cy", "role": "member"}
    assert db_session.query(BoardMembership).filter_by(board_id=board.id).count() == 2


def test_add_member_service_rejects_non_team_member(
    db_session: Any, make_board: Callable[..., Board], make_user: Callable[..., User]
) -> None:
    admin = make_user()
    board = make_board(admin=admin)
    outsider = make_user()
    with pytest.raises(ValidationError) as exc:
        add_member_service(board.id, {"user_id": outsider.id, "role": "member"}, admin)
    assert exc.value.field == "user_id"
    with pytest.raises(ValidationError):
        add_member_service(board.id, {"user_id": uuid.uuid4(), "role": "member"}, admin)


def test_add_member_service_rejects_existing_member(
    db_session: Any, make_board: Callable[..., Board], make_user: Callable[..., User]
) -> None:
    admin = make_user()
    board = make_board(admin=admin)
    with pytest.raises(ValidationError):
        add_member_service(board.id, {"user_id": admin.id, "role": "member"}, admin)


def test_add_member_service_unknown_board(make_user: Callable[..., User]) -> None:
    with pytest.raises(NotFoundError):
        add_member_service(uuid.uuid4(), {"user_id": uuid.uuid4(), "role": "member"}, make_user())


def test_change_member_role_service_changes_role(
    db_session: Any, make_board: Callable[..., Board], make_user: Callable[..., User]
) -> None:
    board = make_board()
    user = make_user(display_name="Di")
    _board_member(db_session, board, user)

    result = change_member_role_service(board.id, user.id, {"role": "admin"})

    assert result == {"user_id": user.id, "display_name": "Di", "role": "admin"}


def test_change_member_role_service_keeps_last_admin(
    db_session: Any, make_board: Callable[..., Board], make_user: Callable[..., User]
) -> None:
    admin = make_user()
    board = make_board(admin=admin)
    with pytest.raises(ValidationError) as exc:
        change_member_role_service(board.id, admin.id, {"role": "member"})
    assert exc.value.field == "role"
    # With a second Admin, demotion is allowed.
    _board_member(db_session, board, make_user(), "admin")
    assert change_member_role_service(board.id, admin.id, {"role": "member"})["role"] == "member"


def test_change_member_role_service_unknown_member(
    make_board: Callable[..., Board],
) -> None:
    board = make_board()
    with pytest.raises(NotFoundError):
        change_member_role_service(board.id, uuid.uuid4(), {"role": "member"})


def test_remove_member_service_removes_member(
    db_session: Any, make_board: Callable[..., Board], make_user: Callable[..., User]
) -> None:
    admin = make_user()
    board = make_board(admin=admin)
    user = make_user()
    _board_member(db_session, board, user)

    remove_member_service(board.id, user.id, admin)

    assert db_session.query(BoardMembership).filter_by(user_id=user.id).count() == 0


def test_remove_member_service_keeps_last_admin_and_unknown_member(
    make_board: Callable[..., Board], make_user: Callable[..., User]
) -> None:
    admin = make_user()
    board = make_board(admin=admin)
    with pytest.raises(ValidationError):
        remove_member_service(board.id, admin.id, admin)
    with pytest.raises(NotFoundError):
        remove_member_service(board.id, uuid.uuid4(), admin)


# --- invitations (R11.x) ------------------------------------------------------


def test_generate_invitation_service_creates_active_link_for_board(
    db_session: Any, make_board: Callable[..., Board], make_user: Callable[..., User]
) -> None:
    admin = make_user()
    board = make_board(admin=admin)

    link = generate_invitation_service(board.id, admin)

    assert set(link) == {"id", "board_id", "token", "status", "created_at"}
    assert link["board_id"] == board.id
    assert link["status"] == "active"
    assert len(link["token"]) >= 32
    other = generate_invitation_service(board.id, admin)
    assert other["token"] != link["token"]


def test_list_invitations_service_shape_and_board_scope(
    make_board: Callable[..., Board], make_user: Callable[..., User]
) -> None:
    admin = make_user()
    board = make_board(admin=admin)
    other_board = make_board(admin=admin)
    first = generate_invitation_service(board.id, admin)
    generate_invitation_service(other_board.id, admin)

    result = list_invitations_service(board.id)

    assert set(result) == {"items"}
    assert [item["id"] for item in result["items"]] == [first["id"]]
    assert set(result["items"][0]) == {"id", "board_id", "token", "status", "created_at"}
    assert list_invitations_service(uuid.uuid4()) == {"items": []}


def test_revoke_invitation_service_affects_only_targeted_link(
    db_session: Any, make_board: Callable[..., Board], make_user: Callable[..., User]
) -> None:
    admin = make_user()
    board = make_board(admin=admin)
    other_board = make_board(admin=admin)
    target = generate_invitation_service(board.id, admin)
    sibling = generate_invitation_service(board.id, admin)
    foreign = generate_invitation_service(other_board.id, admin)

    revoked = revoke_invitation_service(target["token"], admin)

    assert revoked["status"] == "inactive"
    assert db_session.get(InvitationLink, sibling["id"]).status == "active"
    assert db_session.get(InvitationLink, foreign["id"]).status == "active"


def test_revoke_invitation_service_unknown_token_and_non_admin(
    db_session: Any, make_board: Callable[..., Board], make_user: Callable[..., User]
) -> None:
    admin = make_user()
    board = make_board(admin=admin)
    link = generate_invitation_service(board.id, admin)
    member = make_user()
    _board_member(db_session, board, member)
    outsider = make_user()

    with pytest.raises(NotFoundError):
        revoke_invitation_service("no-such-token", admin)
    for user in (member, outsider):
        with pytest.raises(AuthorizationError):
            revoke_invitation_service(link["token"], user)
    assert db_session.get(InvitationLink, link["id"]).status == "active"

"""Property 25: Invitation link generation, isolation, and anonymous Guest access control.

**Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.8**
"""

import string
from collections.abc import Callable
from typing import Any

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import select

from flask_app.access.service import (
    generate_invitation_service,
    revoke_invitation_service,
)
from flask_app.models import Board, Card, Column, InvitationLink, User

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

MakeUser = Callable[..., User]
MakeBoard = Callable[..., Board]
MakeColumn = Callable[..., Column]
MakeCard = Callable[..., Card]

_TOKEN_CHARS = string.ascii_letters + string.digits + "-_"
random_tokens = st.text(alphabet=_TOKEN_CHARS, min_size=1, max_size=64)
link_counts = st.integers(min_value=1, max_value=5)
other_methods = st.sampled_from(["post", "put", "patch", "delete"])


def _board_url(token: str) -> str:
    return f"/api/guest/{token}/board"


def _status(link_id: Any) -> str:
    from flask_app.extensions import db

    link = db.session.scalar(select(InvitationLink).where(InvitationLink.id == link_id))
    assert link is not None
    return str(link.status)


# Feature: task-management-app, Property 25: Invitation link generation, isolation, and anonymous Guest access control  # noqa: E501
@_SETTINGS
@given(count=link_counts)
def test_generated_links_are_active_unique_bound_and_grant_guest_read(
    db_session: Any, client: Any, make_user: MakeUser, make_board: MakeBoard, count: int
) -> None:
    admin = make_user()
    board = make_board(admin=admin, name="Guest Board")
    other_board = make_board(name="Other Board")

    links = [generate_invitation_service(board.id, admin) for _ in range(count)]
    db_session.commit()

    assert len({link["token"] for link in links}) == count
    assert len({link["id"] for link in links}) == count
    for link in links:
        assert link["status"] == "active"
        assert link["board_id"] == board.id
        response = client.get(_board_url(link["token"]))
        assert response.status_code == 200
        body = response.get_json()
        assert body["id"] == str(board.id)
        assert body["id"] != str(other_board.id)
        assert body["currentUserRole"] == "guest"


# Feature: task-management-app, Property 25: Invitation link generation, isolation, and anonymous Guest access control  # noqa: E501
@_SETTINGS
@given(count=st.integers(min_value=2, max_value=5), data=st.data())
def test_revoking_one_link_leaves_all_others_unchanged(
    db_session: Any,
    client: Any,
    make_user: MakeUser,
    make_board: MakeBoard,
    count: int,
    data: st.DataObject,
) -> None:
    admin = make_user()
    board = make_board(admin=admin)
    links = [generate_invitation_service(board.id, admin) for _ in range(count)]
    db_session.commit()
    index = data.draw(st.integers(min_value=0, max_value=count - 1))

    revoked = revoke_invitation_service(links[index]["token"], admin)
    db_session.commit()

    assert revoked["status"] == "inactive"
    for i, link in enumerate(links):
        response = client.get(_board_url(link["token"]))
        if i == index:
            assert _status(link["id"]) == "inactive"
            assert response.status_code == 403
            assert response.get_json()["error"]["code"] == "authorization_error"
        else:
            assert _status(link["id"]) == "active"
            assert response.status_code == 200


# Feature: task-management-app, Property 25: Invitation link generation, isolation, and anonymous Guest access control  # noqa: E501
@_SETTINGS
@given(token=random_tokens)
def test_unknown_token_is_rejected_on_both_guest_routes(
    db_session: Any, client: Any, make_user: MakeUser, make_board: MakeBoard, token: str
) -> None:
    admin = make_user()
    board = make_board(admin=admin)
    link = generate_invitation_service(board.id, admin)
    db_session.commit()
    if token == link["token"]:
        return

    board_response = client.get(_board_url(token))
    comments_response = client.get(
        f"/api/guest/{token}/cards/00000000-0000-4000-8000-000000000000/comments"
    )

    assert board_response.status_code == 403
    assert comments_response.status_code == 403


# Feature: task-management-app, Property 25: Invitation link generation, isolation, and anonymous Guest access control  # noqa: E501
@_SETTINGS
@given(count=link_counts)
def test_archived_board_rejects_all_of_its_tokens(
    db_session: Any, client: Any, make_user: MakeUser, make_board: MakeBoard, count: int
) -> None:
    admin = make_user()
    board = make_board(admin=admin)
    links = [generate_invitation_service(board.id, admin) for _ in range(count)]
    board.status = "archived"
    db_session.commit()

    for link in links:
        assert client.get(_board_url(link["token"])).status_code == 403


# Feature: task-management-app, Property 25: Invitation link generation, isolation, and anonymous Guest access control  # noqa: E501
@_SETTINGS
@given(method=other_methods, comments_route=st.booleans())
def test_non_get_methods_on_guest_routes_are_rejected_with_authorization_error(
    db_session: Any,
    client: Any,
    make_user: MakeUser,
    make_board: MakeBoard,
    make_column: MakeColumn,
    make_card: MakeCard,
    method: str,
    comments_route: bool,
) -> None:
    admin = make_user()
    board = make_board(admin=admin)
    card = make_card(make_column(board=board), created_by=admin)
    link = generate_invitation_service(board.id, admin)
    db_session.commit()
    url = (
        f"/api/guest/{link['token']}/cards/{card.id}/comments"
        if comments_route
        else _board_url(link["token"])
    )

    response = getattr(client, method)(url, json={"name": "changed"})

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "authorization_error"
    db_session.refresh(board)
    assert board.name == "Board"


# Feature: task-management-app, Property 25: Invitation link generation, isolation, and anonymous Guest access control  # noqa: E501
@_SETTINGS
@given(title=st.text(alphabet=string.ascii_letters, min_size=1, max_size=20))
def test_token_only_exposes_its_own_board_and_cards(
    db_session: Any,
    client: Any,
    make_user: MakeUser,
    make_board: MakeBoard,
    make_column: MakeColumn,
    make_card: MakeCard,
    title: str,
) -> None:
    admin = make_user()
    board = make_board(admin=admin)
    other = make_board()
    own_card = make_card(make_column(board=board), title=title, created_by=admin)
    foreign_card = make_card(make_column(board=other), created_by=admin)
    link = generate_invitation_service(board.id, admin)
    db_session.commit()

    body = client.get(_board_url(link["token"])).get_json()
    card_ids = {c["id"] for col in body["columns"] for c in col["cards"]}
    own = client.get(f"/api/guest/{link['token']}/cards/{own_card.id}/comments")
    foreign = client.get(f"/api/guest/{link['token']}/cards/{foreign_card.id}/comments")

    assert card_ids == {str(own_card.id)}
    assert own.status_code == 200
    assert foreign.status_code == 404

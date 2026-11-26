"""Unit tests for the cards service (R3.1-R3.10, R13.1-R13.6, R8.1, R8.2, R8.5)."""

from collections.abc import Callable
from typing import Any

import pytest
from sqlalchemy import select

from flask_app.auth.service import create_access_token
from flask_app.cards.schema import CreateCardSchema, UpdateCardSchema
from flask_app.cards.service import (
    create_card_service,
    delete_card_service,
    get_card_service,
    move_card_service,
    update_card_service,
)
from flask_app.common.exceptions import ConflictError, NotFoundError, ValidationError
from flask_app.common.validation import load_schema
from flask_app.models import ActivityEntry, Board, BoardMembership, Card, Column, User


def test_create_card_appends_with_version_one(
    db_session: Any, make_user: Callable[..., User], make_column: Callable[..., Column]
) -> None:
    user = make_user()
    column = make_column()
    first = create_card_service(column.id, {"title": "A"}, user)
    second = create_card_service(column.id, {"title": "B"}, user)
    assert (first["order_index"], second["order_index"]) == (0, 1)
    assert second["version"] == 1
    assert second["created_at"] == second["updated_at"]
    assert second["created_by_id"] == user.id


def test_create_card_unknown_column_is_not_found(
    db_session: Any, make_user: Callable[..., User]
) -> None:
    import uuid

    with pytest.raises(NotFoundError):
        create_card_service(uuid.uuid4(), {"title": "A"}, make_user())


def test_get_card_includes_version(db_session: Any, make_card: Callable[..., Card]) -> None:
    card = make_card()
    assert get_card_service(card.id)["version"] == 1


def test_get_card_missing_is_not_found(db_session: Any) -> None:
    import uuid

    with pytest.raises(NotFoundError):
        get_card_service(uuid.uuid4())


def test_update_card_increments_version_and_sets_updated_at(
    db_session: Any, make_user: Callable[..., User], make_card: Callable[..., Card]
) -> None:
    user = make_user()
    card = make_card(title="Old")
    before = card.updated_at
    result = update_card_service(card.id, {"title": "New", "version": 1}, user)
    assert result["title"] == "New"
    assert result["version"] == 2
    assert result["updated_at"] >= before


def test_update_card_stale_or_missing_version_conflicts(
    db_session: Any, make_user: Callable[..., User], make_card: Callable[..., Card]
) -> None:
    user = make_user()
    card = make_card(title="Old")
    with pytest.raises(ConflictError):
        update_card_service(card.id, {"title": "X"}, user)
    with pytest.raises(ConflictError):
        update_card_service(card.id, {"title": "X", "version": 5}, user)
    assert db_session.get(Card, card.id).title == "Old"


def test_update_card_assignee_must_be_board_member(
    db_session: Any,
    make_user: Callable[..., User],
    make_board: Callable[..., Board],
    make_column: Callable[..., Column],
    make_card: Callable[..., Card],
) -> None:
    admin = make_user()
    outsider = make_user()
    member = make_user()
    board = make_board(admin=admin)
    db_session.add(BoardMembership(board_id=board.id, user_id=member.id, role="member"))
    db_session.flush()
    card = make_card(column=make_column(board=board), title="Keep")
    with pytest.raises(ValidationError):
        update_card_service(
            card.id, {"title": "Changed", "assignee_id": outsider.id, "version": 1}, admin
        )
    assert db_session.get(Card, card.id).title == "Keep"
    result = update_card_service(card.id, {"assignee_id": member.id, "version": 1}, admin)
    assert result["assignee_id"] == member.id


def test_delete_card_reindexes_and_records_activity(
    db_session: Any,
    make_user: Callable[..., User],
    make_column: Callable[..., Column],
    make_card: Callable[..., Card],
) -> None:
    user = make_user()
    column = make_column()
    cards = [make_card(column=column, title=f"C{i}") for i in range(3)]
    delete_card_service(cards[0].id, user)
    remaining = db_session.scalars(
        select(Card).where(Card.column_id == column.id).order_by(Card.order_index)
    ).all()
    assert [c.order_index for c in remaining] == [0, 1]
    assert [c.title for c in remaining] == ["C1", "C2"]
    with pytest.raises(NotFoundError):
        delete_card_service(cards[0].id, user)


def test_card_mutations_record_activity(
    db_session: Any, make_user: Callable[..., User], make_column: Callable[..., Column]
) -> None:
    user = make_user()
    column = make_column()
    card = create_card_service(column.id, {"title": "T"}, user)
    update_card_service(card["id"], {"description": "d", "version": 1}, user)
    delete_card_service(card["id"], user)
    entries = db_session.scalars(
        select(ActivityEntry).where(ActivityEntry.board_id == column.board_id)
    ).all()
    assert sorted(e.event_type for e in entries) == ["card_created", "card_deleted", "card_updated"]
    assert all(e.actor_id == user.id and e.resource_id == card["id"] for e in entries)


@pytest.mark.parametrize("title", ["", "   ", "x" * 256])
def test_invalid_title_is_rejected(title: str) -> None:
    with pytest.raises(ValidationError):
        load_schema(CreateCardSchema(), {"title": title})
    with pytest.raises(ValidationError):
        load_schema(UpdateCardSchema(), {"title": title, "version": 1})


def test_update_schema_version_optional_but_strict() -> None:
    assert "version" not in load_schema(UpdateCardSchema(), {"title": "a"})
    with pytest.raises(ValidationError):
        load_schema(UpdateCardSchema(), {"version": "1"})
    with pytest.raises(ValidationError):
        load_schema(UpdateCardSchema(), {"description": "x" * 5001, "version": 1})


def _titles(db_session: Any, column: Column) -> list[str]:
    db_session.expire_all()
    rows = db_session.scalars(
        select(Card).where(Card.column_id == column.id).order_by(Card.order_index)
    ).all()
    assert [c.order_index for c in rows] == list(range(len(rows)))
    return [c.title for c in rows]


def test_move_card_reorders_within_column(
    db_session: Any,
    make_user: Callable[..., User],
    make_column: Callable[..., Column],
    make_card: Callable[..., Card],
) -> None:
    column = make_column()
    cards = [make_card(column=column, title=t) for t in "ABC"]
    result = move_card_service(cards[0].id, column.id, 2, make_user())
    assert result["order_index"] == 2
    assert _titles(db_session, column) == ["B", "C", "A"]


def test_move_card_across_columns_reindexes_both(
    db_session: Any,
    make_user: Callable[..., User],
    make_board: Callable[..., Board],
    make_column: Callable[..., Column],
    make_card: Callable[..., Card],
) -> None:
    board = make_board()
    src, dst = make_column(board=board), make_column(board=board, name="Doing")
    a, b = make_card(column=src, title="A"), make_card(column=src, title="B")
    make_card(column=dst, title="X")
    result = move_card_service(a.id, dst.id, 0, make_user())
    assert result["column_id"] == dst.id
    assert _titles(db_session, src) == ["B"]
    assert _titles(db_session, dst) == ["A", "X"]
    assert b.id


@pytest.mark.parametrize("index", [-1, 2, True, "0", 1.0])
def test_move_card_rejects_bad_index(
    db_session: Any,
    make_user: Callable[..., User],
    make_column: Callable[..., Column],
    make_card: Callable[..., Card],
    index: Any,
) -> None:
    column = make_column()
    card = make_card(column=column, title="A")
    make_card(column=column, title="B")
    with pytest.raises(ValidationError):
        move_card_service(card.id, column.id, index, make_user())
    assert _titles(db_session, column) == ["A", "B"]


def test_move_card_rejects_column_of_other_board(
    db_session: Any,
    make_user: Callable[..., User],
    make_column: Callable[..., Column],
    make_card: Callable[..., Card],
) -> None:
    card = make_card()
    other = make_column()
    with pytest.raises(ValidationError):
        move_card_service(card.id, other.id, 0, make_user())


def test_move_card_touches_only_moved_card_and_keeps_version(
    db_session: Any,
    clock: Any,
    make_user: Callable[..., User],
    make_column: Callable[..., Column],
    make_card: Callable[..., Card],
) -> None:
    column = make_column()
    a, b = make_card(column=column, title="A"), make_card(column=column, title="B")
    stamps = (a.updated_at, b.updated_at)
    clock.advance(hours=1)
    move_card_service(a.id, column.id, 1, make_user())
    db_session.expire_all()
    moved, shifted = db_session.get(Card, a.id), db_session.get(Card, b.id)
    assert moved.updated_at > stamps[0]
    assert shifted.updated_at == stamps[1]
    assert moved.version == 1 and shifted.version == 1


def test_move_card_records_activity_once(
    db_session: Any,
    make_user: Callable[..., User],
    make_column: Callable[..., Column],
    make_card: Callable[..., Card],
) -> None:
    column = make_column()
    card = make_card(column=column)
    user = make_user()
    move_card_service(card.id, column.id, 0, user)
    entries = db_session.scalars(
        select(ActivityEntry).where(ActivityEntry.event_type == "card_moved")
    ).all()
    assert len(entries) == 1
    assert entries[0].actor_id == user.id and entries[0].resource_id == card.id


def test_move_route_rejects_guest_non_member_and_anonymous(
    db_session: Any,
    client: Any,
    make_user: Callable[..., User],
    make_column: Callable[..., Column],
    make_card: Callable[..., Card],
) -> None:
    column = make_column()
    card = make_card(column=column)
    outsider = make_user()
    body = {"targetColumnId": str(column.id), "targetIndex": 0}
    url = f"/api/cards/{card.id}/move"
    db_session.commit()  # error handlers roll back; keep the fixtures
    assert client.post(url, json=body).status_code == 401
    client.set_cookie("access_token", create_access_token(outsider.id))
    assert client.post(url, json=body).status_code == 403
    db_session.add(BoardMembership(board_id=column.board_id, user_id=outsider.id, role="member"))
    db_session.commit()
    assert client.post(url, json=body).status_code == 200
    assert client.post(url, json={**body, "version": 1}).status_code == 400


def test_guest_path_rejects_non_get_card_requests_with_403(
    db_session: Any, client: Any, make_card: Callable[..., Card]
) -> None:
    card = make_card()
    db_session.commit()
    for method in ("post", "patch", "delete"):
        response = getattr(client, method)(f"/api/guest/some-token/cards/{card.id}", json={})
        assert response.status_code == 403
        assert response.get_json()["error"]["code"] == "authorization_error"


def test_card_routes_reject_missing_cookie_and_non_member(
    db_session: Any,
    client: Any,
    make_user: Callable[..., User],
    make_column: Callable[..., Column],
    make_card: Callable[..., Card],
) -> None:
    column = make_column()
    card = make_card(column=column)
    outsider = make_user()
    db_session.commit()
    for method, url in (
        ("post", f"/api/columns/{column.id}/cards"),
        ("get", f"/api/cards/{card.id}"),
        ("patch", f"/api/cards/{card.id}"),
        ("delete", f"/api/cards/{card.id}"),
    ):
        anonymous = getattr(client, method)(url, json={"title": "T", "version": 1})
        assert anonymous.status_code == 401
        assert anonymous.get_json()["error"]["code"] == "authentication_error"
    client.set_cookie("access_token", create_access_token(outsider.id))
    forbidden = client.get(f"/api/cards/{card.id}")
    assert forbidden.status_code == 403
    assert forbidden.get_json()["error"]["code"] == "authorization_error"

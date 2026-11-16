"""Unit tests for the boards service (R1.2, R1.4, R1.5, R1.7, R1.8, R1.9)."""

from collections.abc import Callable
from typing import Any

import pytest
from sqlalchemy import select

from flask_app.access.rbac import COLUMN_MANAGE, get_board_role, role_allows
from flask_app.boards.schema import CreateBoardSchema, UpdateBoardSchema
from flask_app.boards.service import (
    archive_board_service,
    create_board_service,
    list_boards_service,
    restore_board_service,
    update_board_service,
)
from flask_app.common.exceptions import AuthorizationError, ValidationError
from flask_app.common.validation import load_schema
from flask_app.models import Board, BoardMembership, Column, Team, User


def test_create_board_adds_default_columns_in_order(
    db_session: Any, make_user: Callable[..., User], make_team: Callable[..., Team]
) -> None:
    creator = make_user()
    team = make_team(admin=creator)
    result = create_board_service({"team_id": team.id, "name": "Sprint"}, creator)
    columns = db_session.scalars(
        select(Column).where(Column.board_id == result["id"]).order_by(Column.order_index)
    ).all()
    assert [(c.name, c.order_index) for c in columns] == [
        ("To Do", 0),
        ("Doing", 1),
        ("Done", 2),
    ]
    assert result["current_user_role"] == "admin"
    membership = db_session.scalar(
        select(BoardMembership).where(
            BoardMembership.board_id == result["id"], BoardMembership.user_id == creator.id
        )
    )
    assert membership is not None
    assert membership.role == "admin"


def test_create_board_rejects_non_team_member(
    db_session: Any, make_user: Callable[..., User], make_team: Callable[..., Team]
) -> None:
    team = make_team()
    with pytest.raises(AuthorizationError):
        create_board_service({"team_id": team.id, "name": "Nope"}, make_user())


def test_archive_hides_board_from_active_list_and_restore_returns_it(
    db_session: Any, make_user: Callable[..., User], make_board: Callable[..., Board]
) -> None:
    admin = make_user()
    board = make_board(admin=admin)

    archived = archive_board_service(board.id, admin)
    assert archived["status"] == "archived"
    assert list_boards_service({}, admin)["items"] == []
    archived_items = list_boards_service({"archived": True}, admin)["items"]
    assert [item["id"] for item in archived_items] == [board.id]

    restored = restore_board_service(board.id, admin)
    assert restored["status"] == "active"
    assert [item["id"] for item in list_boards_service({}, admin)["items"]] == [board.id]


def test_restore_non_archived_board_raises_validation_error(
    db_session: Any, make_user: Callable[..., User], make_board: Callable[..., Board]
) -> None:
    admin = make_user()
    board = make_board(admin=admin)
    with pytest.raises(ValidationError):
        restore_board_service(board.id, admin)


def test_update_board_changes_only_provided_fields(
    db_session: Any, make_user: Callable[..., User], make_board: Callable[..., Board]
) -> None:
    admin = make_user()
    board = make_board(admin=admin, name="Old", description="keep")
    result = update_board_service(board.id, {"name": "New"}, admin)
    assert result["name"] == "New"
    assert result["description"] == "keep"


def test_non_admin_roles_cannot_manage_board(
    db_session: Any, make_user: Callable[..., User], make_board: Callable[..., Board]
) -> None:
    admin = make_user()
    board = make_board(admin=admin)
    member = make_user()
    db_session.add(BoardMembership(board_id=board.id, user_id=member.id, role="member"))
    db_session.flush()
    outsider = make_user()

    assert role_allows(get_board_role(board.id, admin.id), COLUMN_MANAGE)
    assert not role_allows(get_board_role(board.id, member.id), COLUMN_MANAGE)
    assert not role_allows(get_board_role(board.id, outsider.id), COLUMN_MANAGE)
    assert not role_allows("guest", COLUMN_MANAGE)


@pytest.mark.parametrize("name", ["", "   ", "x" * 101])
def test_invalid_name_rejected_on_create_and_update(name: str, db_session: Any) -> None:
    with pytest.raises(ValidationError):
        load_schema(
            CreateBoardSchema(), {"team_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7", "name": name}
        )
    with pytest.raises(ValidationError):
        load_schema(UpdateBoardSchema(), {"name": name})


def test_name_is_trimmed_and_100_chars_accepted() -> None:
    loaded = load_schema(UpdateBoardSchema(), {"name": "  " + "x" * 100 + "  "})
    assert loaded["name"] == "x" * 100

"""Unit tests for the columns service (R2.1, R2.2, R2.6, R2.7, R2.8, R8.8, R8.9)."""

from collections.abc import Callable
from typing import Any

import pytest
from sqlalchemy import select

from flask_app.access.rbac import COLUMN_MANAGE, get_board_role, role_allows
from flask_app.columns.schema import CreateColumnSchema, RenameColumnSchema
from flask_app.columns.service import (
    create_column_service,
    delete_column_service,
    rename_column_service,
    reorder_column_service,
)
from flask_app.common.exceptions import ValidationError
from flask_app.common.validation import load_schema
from flask_app.models import ActivityEntry, Board, BoardMembership, Column, User


def test_create_column_appends_at_end(
    db_session: Any, make_user: Callable[..., User], make_board: Callable[..., Board]
) -> None:
    admin = make_user()
    board = make_board(admin=admin)
    count = db_session.query(Column).filter(Column.board_id == board.id).count()
    assert count == 0
    first = create_column_service(board.id, {"name": "A"}, admin)
    second = create_column_service(board.id, {"name": "B"}, admin)
    assert first["order_index"] == 0
    assert second["order_index"] == 1


def test_rename_column_changes_name(db_session: Any, make_column: Callable[..., Column]) -> None:
    column = make_column(name="Old")
    result = rename_column_service(column.id, {"name": "New"})
    assert result["name"] == "New"
    assert db_session.get(Column, column.id).name == "New"


@pytest.mark.parametrize("schema", [CreateColumnSchema, RenameColumnSchema])
@pytest.mark.parametrize("name", ["", "   ", "x" * 101])
def test_invalid_column_name_is_rejected(schema: Any, name: str) -> None:
    with pytest.raises(ValidationError):
        load_schema(schema(), {"name": name})


@pytest.mark.parametrize("schema", [CreateColumnSchema, RenameColumnSchema])
def test_valid_column_name_is_trimmed(schema: Any) -> None:
    assert load_schema(schema(), {"name": "  " + "x" * 100 + " "})["name"] == "x" * 100


@pytest.mark.parametrize("target", [-1, 3])
def test_reorder_out_of_range_is_rejected(
    db_session: Any,
    make_board: Callable[..., Board],
    make_column: Callable[..., Column],
    target: int,
) -> None:
    board = make_board()
    columns = [make_column(board=board, name=f"C{i}") for i in range(3)]
    with pytest.raises(ValidationError):
        reorder_column_service(columns[0].id, {"target_index": target})
    assert [c.order_index for c in columns] == [0, 1, 2]


def test_reorder_moves_column_and_keeps_indexes_contiguous(
    db_session: Any, make_board: Callable[..., Board], make_column: Callable[..., Column]
) -> None:
    board = make_board()
    columns = [make_column(board=board, name=f"C{i}") for i in range(3)]
    reorder_column_service(columns[0].id, {"target_index": 2})
    ordered = db_session.scalars(
        select(Column).where(Column.board_id == board.id).order_by(Column.order_index)
    ).all()
    assert [c.name for c in ordered] == ["C1", "C2", "C0"]
    assert [c.order_index for c in ordered] == [0, 1, 2]


def test_non_admin_roles_cannot_manage_columns(
    db_session: Any, make_user: Callable[..., User], make_board: Callable[..., Board]
) -> None:
    admin = make_user()
    member = make_user()
    outsider = make_user()
    board = make_board(admin=admin)
    db_session.add(BoardMembership(board_id=board.id, user_id=member.id, role="member"))
    db_session.flush()
    assert role_allows(get_board_role(board.id, admin.id), COLUMN_MANAGE)
    assert not role_allows(get_board_role(board.id, member.id), COLUMN_MANAGE)
    assert not role_allows(get_board_role(board.id, outsider.id), COLUMN_MANAGE)


def test_create_and_delete_record_activity(
    db_session: Any, make_user: Callable[..., User], make_board: Callable[..., Board]
) -> None:
    admin = make_user()
    board = make_board(admin=admin)
    column = create_column_service(board.id, {"name": "Temp"}, admin)
    delete_column_service(column["id"], admin)
    entries = db_session.scalars(
        select(ActivityEntry).where(ActivityEntry.board_id == board.id)
    ).all()
    assert sorted(e.event_type for e in entries) == ["column_created", "column_deleted"]
    assert all(e.actor_id == admin.id and e.resource_id == column["id"] for e in entries)

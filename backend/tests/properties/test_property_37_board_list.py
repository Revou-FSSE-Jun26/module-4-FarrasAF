"""Property 37: Board list reflects the caller's Board roles and the archived filter.

**Validates: Requirements 1.13**
"""

from collections.abc import Callable
from typing import Any

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from flask_app.boards.service import list_boards_service
from flask_app.extensions import db
from flask_app.models import Board, BoardMembership, User

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

# (caller's role on the Board or None for no membership, Board status)
board_specs = st.lists(
    st.tuples(st.sampled_from(["admin", "member", None]), st.sampled_from(["active", "archived"])),
    max_size=8,
)

MakeUser = Callable[..., User]
MakeBoard = Callable[..., Board]


# Feature: task-management-app, Property 37: Board list reflects the caller's Board roles and the archived filter  # noqa: E501
@_SETTINGS
@given(specs=board_specs, archived=st.booleans())
def test_board_list_reflects_roles_and_archived_filter(
    db_session: Any,
    make_user: MakeUser,
    make_board: MakeBoard,
    specs: list[tuple[str | None, str]],
    archived: bool,
) -> None:
    caller = make_user()
    expected: dict[Any, str] = {}
    for role, status in specs:
        board = make_board(status=status)
        if role is not None:
            db_session.add(BoardMembership(board_id=board.id, user_id=caller.id, role=role))
        wanted = (status == "archived" and role == "admin") if archived else (status == "active")
        if wanted and role is not None:
            expected[board.id] = role
    db.session.flush()

    result = list_boards_service({"archived": archived}, caller)

    items = result["items"]
    assert len(items) == len(expected)
    assert {item["id"] for item in items} == set(expected)
    for item in items:
        assert item["current_user_role"] == expected[item["id"]]
        assert item["status"] == ("archived" if archived else "active")

"""Property 36: Activity is readable only by Members and Admins.

**Validates: Requirements 8.14**
"""

import uuid
from collections.abc import Callable
from typing import Any

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from flask_app.auth.service import create_access_token
from flask_app.models import ActivityEntry, Board, BoardMembership, TeamMembership, User

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)

_READERS = ("admin", "member")
_DENIED = ("team_non_member_of_board", "outsider", "unauthenticated_guest")


# Feature: task-management-app, Property 36: Activity is readable only by Members and Admins
@_SETTINGS
@given(
    role=st.sampled_from(_READERS + _DENIED),
    entry_count=st.integers(0, 5),
    page=st.integers(0, 3),
)
def test_activity_is_readable_only_by_members_and_admins(
    db_session: Any,
    client: Any,
    make_user: Callable[..., User],
    make_board: Callable[..., Board],
    role: str,
    entry_count: int,
    page: int,
) -> None:
    board_admin = make_user()
    board = make_board(admin=board_admin)
    for _ in range(entry_count):
        db_session.add(
            ActivityEntry(
                board_id=board.id,
                actor_id=board_admin.id,
                event_type="card_created",
                resource_id=uuid.uuid4(),
            )
        )
    db_session.flush()

    caller: User | None
    if role == "admin":
        caller = board_admin
    elif role == "member":
        caller = make_user()
        db_session.add(
            TeamMembership(team_id=board.team_id, user_id=caller.id, team_role="team_regular")
        )
        db_session.add(BoardMembership(board_id=board.id, user_id=caller.id, role="member"))
    elif role == "team_non_member_of_board":
        caller = make_user()
        db_session.add(
            TeamMembership(team_id=board.team_id, user_id=caller.id, team_role="team_regular")
        )
    elif role == "outsider":
        caller = make_user()
    else:  # a Guest has no account, so the request carries no credentials
        caller = None
    db_session.flush()

    client.delete_cookie("access_token")
    if caller is not None:
        client.set_cookie("access_token", create_access_token(caller.id))

    response = client.get(f"/api/boards/{board.id}/activity", query_string={"page": page})
    body = response.get_json()

    if role in _READERS:
        assert response.status_code == 200
        # Only page 0 can hold the (at most 5) entries.
        assert len(body["items"]) == (entry_count if page == 0 else 0)
    else:
        assert response.status_code == (401 if caller is None else 403)
        assert "items" not in body
        assert "error" in body

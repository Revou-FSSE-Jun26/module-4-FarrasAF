"""Property 13: Mentions create exactly one unread notification per distinct board member.

**Validates: Requirements 6.1, 6.8**
"""

import uuid
from collections.abc import Callable
from typing import Any

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import select

from flask_app.comments.service import create_comment_service

from flask_app.models import BoardMembership, Card, Notification, User  # isort: skip

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

MakeUser = Callable[..., User]


# Feature: task-management-app, Property 13: Mentions create exactly one unread notification per distinct board member  # noqa: E501
@_SETTINGS
@given(
    member_count=st.integers(0, 4),
    outsider_count=st.integers(0, 3),
    picks=st.lists(st.tuples(st.booleans(), st.integers(0, 3)), max_size=10),
    text=st.text(alphabet="abc xyz", max_size=20),
)
def test_mentions_notify_each_distinct_board_member_once(
    db_session: Any,
    make_user: MakeUser,
    make_board: Callable[..., Any],
    make_column: Callable[..., Any],
    make_card: Callable[..., Card],
    member_count: int,
    outsider_count: int,
    picks: list[tuple[bool, int]],
    text: str,
) -> None:
    author = make_user()
    board = make_board(admin=author)
    members = [make_user() for _ in range(member_count)]
    for m in members:
        db_session.add(BoardMembership(board_id=board.id, user_id=m.id, role="member"))
    outsiders = [make_user() for _ in range(outsider_count)]
    db_session.flush()
    card = make_card(column=make_column(board=board))

    # Mentions of unknown users (not in the database at all) are also ignored.
    ghosts = [uuid.uuid4() for _ in range(2)]
    pool_members: list[uuid.UUID] = [author.id, *(m.id for m in members)]
    pool_others: list[uuid.UUID] = [*(o.id for o in outsiders), *ghosts]

    mentioned: list[uuid.UUID] = []
    for want_member, idx in picks:
        pool = pool_members if want_member else pool_others
        mentioned.append(pool[idx % len(pool)])
    body = f"hi {text} " + " ".join(f"@[{u}]" for u in mentioned) + " end"

    created = create_comment_service(card.id, {"body": body}, author)

    notes = db_session.scalars(
        select(Notification).where(Notification.comment_id == created["id"])
    ).all()
    expected = {u for u in mentioned if u in set(pool_members)}
    recipients = [n.recipient_id for n in notes]

    assert len(recipients) == len(set(recipients))
    assert set(recipients) == expected
    assert all(n.status == "unread" for n in notes)
    assert all(n.board_id == board.id for n in notes)

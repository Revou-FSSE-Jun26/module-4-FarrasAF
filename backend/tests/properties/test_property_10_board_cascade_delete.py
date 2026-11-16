"""Property 10: Board permanent delete cascades completely.

**Validates: Requirements 1.6**
"""

import uuid
from collections.abc import Callable
from typing import Any

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import func, select

from flask_app.boards.service import delete_board_service
from flask_app.models import (
    ActivityEntry,
    Board,
    BoardMembership,
    Card,
    Column,
    Comment,
    InvitationLink,
    Notification,
    User,
)

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

MakeUser = Callable[..., User]
MakeBoard = Callable[..., Board]
MakeColumn = Callable[..., Column]
MakeCard = Callable[..., Card]


@st.composite
def board_shapes(draw: st.DrawFn) -> dict[str, Any]:
    """Shape of a Board's contents: cards and comments per column, plus side tables."""
    return {
        "cards_per_column": draw(st.lists(st.integers(0, 3), min_size=1, max_size=4)),
        "comments_per_card": draw(st.integers(0, 2)),
        "extra_members": draw(st.integers(0, 3)),
        "invitations": draw(st.integers(0, 3)),
        "activity": draw(st.integers(0, 4)),
    }


def _populate(
    db_session: Any,
    board: Board,
    shape: dict[str, Any],
    actor: User,
    make_user: MakeUser,
    make_column: MakeColumn,
    make_card: MakeCard,
) -> None:
    """Fill a Board with Columns, Cards, Comments, Notifications and side rows."""
    recipient = make_user()
    for cards in shape["cards_per_column"]:
        column = make_column(board=board)
        for _ in range(cards):
            card = make_card(column=column, created_by=actor)
            for _ in range(shape["comments_per_card"]):
                comment = Comment(card_id=card.id, author_id=actor.id, body="hello")
                db_session.add(comment)
                db_session.flush()
                db_session.add(
                    Notification(
                        recipient_id=recipient.id, comment_id=comment.id, board_id=board.id
                    )
                )
    for _ in range(shape["extra_members"]):
        db_session.add(BoardMembership(board_id=board.id, user_id=make_user().id, role="member"))
    for _ in range(shape["invitations"]):
        db_session.add(
            InvitationLink(board_id=board.id, token=uuid.uuid4().hex, created_by_id=actor.id)
        )
    for _ in range(shape["activity"]):
        db_session.add(
            ActivityEntry(
                board_id=board.id,
                actor_id=actor.id,
                event_type="card_created",
                resource_id=uuid.uuid4(),
            )
        )
    db_session.flush()


def _counts(db_session: Any, board_id: uuid.UUID) -> dict[str, int]:
    def count(model: Any, where: Any) -> int:
        return int(db_session.scalar(select(func.count()).select_from(model).where(where)) or 0)

    return {
        "boards": count(Board, Board.id == board_id),
        "columns": count(Column, Column.board_id == board_id),
        "cards": count(Card, Card.board_id == board_id),
        "comments": count(
            Comment,
            Comment.card_id.in_(select(Card.id).where(Card.board_id == board_id)),
        ),
        "notifications": count(Notification, Notification.board_id == board_id),
        "memberships": count(BoardMembership, BoardMembership.board_id == board_id),
        "invitations": count(InvitationLink, InvitationLink.board_id == board_id),
        "activity": count(ActivityEntry, ActivityEntry.board_id == board_id),
    }


# Feature: task-management-app, Property 10: Board permanent delete cascades completely
@_SETTINGS
@given(shape=board_shapes(), other_shape=board_shapes())
def test_board_delete_removes_all_dependents_and_leaves_other_boards(
    db_session: Any,
    make_user: MakeUser,
    make_board: MakeBoard,
    make_column: MakeColumn,
    make_card: MakeCard,
    shape: dict[str, Any],
    other_shape: dict[str, Any],
) -> None:
    admin = make_user()
    board = make_board(admin=admin)
    other = make_board(admin=admin)
    _populate(db_session, board, shape, admin, make_user, make_column, make_card)
    _populate(db_session, other, other_shape, admin, make_user, make_column, make_card)
    board_id, other_id = board.id, other.id
    other_before = _counts(db_session, other_id)
    assert _counts(db_session, board_id)["boards"] == 1

    delete_board_service(board_id)
    db_session.expire_all()

    assert all(value == 0 for value in _counts(db_session, board_id).values())
    assert _counts(db_session, other_id) == other_before

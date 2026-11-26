"""Property 12: Reply threading validity.

**Validates: Requirements 5.2, 5.8**
"""

import uuid
from collections.abc import Callable
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import func, select

from flask_app.comments.service import create_comment_service
from flask_app.common.exceptions import ValidationError

from flask_app.models import Card, Comment, User  # isort: skip

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

_BODY = st.text(alphabet="abc xyz", min_size=1, max_size=20).filter(lambda s: s.strip() != "")


def _comment_count(db_session: Any) -> int:
    return int(db_session.scalar(select(func.count()).select_from(Comment)))


# Feature: task-management-app, Property 12: Reply threading validity
@_SETTINGS
@given(
    body=_BODY,
    reply_body=_BODY,
    parent_kind=st.sampled_from(["same_card", "other_card", "missing"]),
)
def test_reply_threading_validity(
    db_session: Any,
    make_user: Callable[..., User],
    make_board: Callable[..., Any],
    make_column: Callable[..., Any],
    make_card: Callable[..., Card],
    body: str,
    reply_body: str,
    parent_kind: str,
) -> None:
    author = make_user()
    board = make_board(admin=author)
    column = make_column(board=board)
    card = make_card(column=column)
    other_card = make_card(column=column)

    parent_same = create_comment_service(card.id, {"body": body}, author)
    parent_other = create_comment_service(other_card.id, {"body": body}, author)
    parent_ids: dict[str, uuid.UUID] = {
        "same_card": parent_same["id"],
        "other_card": parent_other["id"],
        "missing": uuid.uuid4(),
    }
    parent_id = parent_ids[parent_kind]
    before = _comment_count(db_session)

    if parent_kind == "same_card":
        reply = create_comment_service(
            card.id, {"body": reply_body, "parent_comment_id": parent_id}, author
        )
        assert reply["parent_comment_id"] == parent_id
        assert reply["card_id"] == card.id
        assert _comment_count(db_session) == before + 1
        stored = db_session.get(Comment, reply["id"])
        assert stored is not None
        assert stored.parent_comment_id == parent_id
    else:
        with pytest.raises(ValidationError) as exc:
            create_comment_service(
                card.id, {"body": reply_body, "parent_comment_id": parent_id}, author
            )
        assert exc.value.field == "parent_comment_id"
        assert _comment_count(db_session) == before

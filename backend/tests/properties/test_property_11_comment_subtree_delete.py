"""Property 11: Comment deletion removes the entire reply subtree.

**Validates: Requirements 5.4**
"""

from collections.abc import Callable
from typing import Any
from uuid import UUID

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import select

from flask_app.comments.service import create_comment_service, delete_comment_service

from flask_app.models import Card, Comment, User  # isort: skip

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)


def _descendants(children: dict[int, list[int]], root: int) -> set[int]:
    found = {root}
    stack = [root]
    while stack:
        for child in children.get(stack.pop(), []):
            found.add(child)
            stack.append(child)
    return found


# Feature: task-management-app, Property 11: Comment deletion removes the entire reply subtree
@_SETTINGS
@given(
    # parent_choices[i] picks the parent of comment i (negative or i == 0 means top-level)
    parent_choices=st.lists(st.integers(min_value=-5, max_value=1000), min_size=1, max_size=12),
    delete_choice=st.integers(min_value=0, max_value=1000),
)
def test_comment_deletion_removes_entire_subtree(
    db_session: Any,
    make_user: Callable[..., User],
    make_board: Callable[..., Any],
    make_column: Callable[..., Any],
    make_card: Callable[..., Card],
    parent_choices: list[int],
    delete_choice: int,
) -> None:
    author = make_user()
    board = make_board(admin=author)
    card = make_card(column=make_column(board=board))
    other_card = make_card(column=make_column(board=board))

    # A comment on another Card must never be affected.
    bystander = create_comment_service(other_card.id, {"body": "bystander"}, author)

    ids: list[UUID] = []
    children: dict[int, list[int]] = {}
    for i, choice in enumerate(parent_choices):
        parent_index = None if (i == 0 or choice < 0) else choice % i
        payload: dict[str, Any] = {"body": f"comment {i}"}
        if parent_index is not None:
            payload["parent_comment_id"] = ids[parent_index]
            children.setdefault(parent_index, []).append(i)
        ids.append(create_comment_service(card.id, payload, author)["id"])

    target = delete_choice % len(ids)
    removed = _descendants(children, target)

    delete_comment_service(ids[target], author)
    db_session.expire_all()

    remaining = set(db_session.scalars(select(Comment.id).where(Comment.card_id == card.id)).all())
    expected = {ids[i] for i in range(len(ids)) if i not in removed}
    assert remaining == expected
    assert db_session.get(Comment, bystander["id"]) is not None

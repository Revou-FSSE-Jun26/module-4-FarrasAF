"""Unit tests for the search module (R7.1-R7.6)."""

from collections.abc import Callable
from datetime import timedelta
from typing import Any

import pytest

from flask_app.common.exceptions import ValidationError
from flask_app.common.pagination import SEARCH_PAGE_SIZE
from flask_app.common.validation import load_schema
from flask_app.models import Board, BoardMembership, Card, Column, User
from flask_app.search.schema import SearchQuerySchema
from flask_app.search.service import search_cards_service
from tests.conftest import FakeClock


def _search(user: User, q: str) -> list[dict[str, Any]]:
    payload = load_schema(SearchQuerySchema(), {"q": q})
    items: list[dict[str, Any]] = search_cards_service(user, payload)["items"]
    return items


@pytest.fixture
def setup(
    make_user: Callable[..., User],
    make_board: Callable[..., Board],
    make_column: Callable[..., Column],
) -> tuple[User, Board, Column]:
    user = make_user()
    board = make_board(admin=user)
    return user, board, make_column(board=board, name="Doing")


def test_case_insensitive_match_includes_board_and_column(
    setup: tuple[User, Board, Column], make_card: Callable[..., Card]
) -> None:
    user, board, column = setup
    card = make_card(column=column, title="Fix Login Bug")
    make_card(column=column, title="Other")
    items = _search(user, "login")
    assert [i["id"] for i in items] == [card.id]
    assert items[0]["board"] == {"id": board.id, "name": board.name}
    assert items[0]["column"] == {"id": column.id, "name": "Doing"}


@pytest.mark.parametrize("keyword", ["%", "_", "\\", "a%b"])
def test_wildcards_are_literal(
    setup: tuple[User, Board, Column], make_card: Callable[..., Card], keyword: str
) -> None:
    user, _, column = setup
    make_card(column=column, title="plain title")
    make_card(column=column, title="axb")
    literal = make_card(column=column, title=f"x{keyword}y")
    assert [i["id"] for i in _search(user, keyword)] == [literal.id]


def test_inaccessible_boards_excluded(
    setup: tuple[User, Board, Column],
    make_card: Callable[..., Card],
    make_board: Callable[..., Board],
    make_column: Callable[..., Column],
) -> None:
    user, _, column = setup
    mine = make_card(column=column, title="shared word")
    other_column = make_column(board=make_board())
    make_card(column=other_column, title="shared word")
    assert [i["id"] for i in _search(user, "shared")] == [mine.id]


def test_no_match_returns_empty(setup: tuple[User, Board, Column]) -> None:
    assert _search(setup[0], "nothing") == []


@pytest.mark.parametrize("keyword", ["", "   ", "x" * 101])
def test_invalid_keyword_rejected(keyword: str) -> None:
    with pytest.raises(ValidationError):
        load_schema(SearchQuerySchema(), {"q": keyword})


def test_ordering_and_cap(
    setup: tuple[User, Board, Column], make_card: Callable[..., Card], clock: FakeClock
) -> None:
    user, _, column = setup
    created = []
    for i in range(SEARCH_PAGE_SIZE + 5):
        clock.advance(seconds=1)
        created.append(make_card(column=column, title=f"task {i}"))
    items = _search(user, "task")
    assert len(items) == SEARCH_PAGE_SIZE
    assert [i["id"] for i in items] == [c.id for c in reversed(created)][:SEARCH_PAGE_SIZE]


def test_equal_updated_at_ties_break_by_id_desc(
    setup: tuple[User, Board, Column], make_card: Callable[..., Card], clock: FakeClock
) -> None:
    user, _, column = setup
    stamp = clock.now + timedelta(seconds=1)
    cards = [make_card(column=column, title=f"tie {i}", updated_at=stamp) for i in range(4)]
    expected = [c.id for c in sorted(cards, key=lambda c: c.id, reverse=True)]
    assert [i["id"] for i in _search(user, "tie")] == expected


def test_membership_required(
    setup: tuple[User, Board, Column],
    make_card: Callable[..., Card],
    make_user: Callable[..., User],
    db_session: Any,
) -> None:
    _, board, column = setup
    make_card(column=column, title="secret")
    outsider = make_user()
    assert _search(outsider, "secret") == []
    db_session.add(BoardMembership(board_id=board.id, user_id=outsider.id, role="member"))
    db_session.flush()
    assert len(_search(outsider, "secret")) == 1

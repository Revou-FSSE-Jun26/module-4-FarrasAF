"""Property 16: Search result soundness, completeness, content, ordering, and cap.

**Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.6**
"""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from flask_app.common.pagination import SEARCH_PAGE_SIZE
from flask_app.models import Board, Card, Column, User
from flask_app.search.service import search_cards_service

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)

_BASE_TIME = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)

# Small ASCII alphabet that includes the LIKE metacharacters, so wildcard bugs and
# case-insensitivity are both exercised (ASCII keeps Python and ILIKE case folding equal).
_ALPHABET = "aAbB%_\\x"
_KEYWORD = st.text(alphabet=_ALPHABET, min_size=1, max_size=100)
_FILLER = st.text(alphabet=_ALPHABET, max_size=10)


@st.composite
def _card_spec(draw: st.DrawFn, keyword: str) -> tuple[str, bool, int]:
    """(title, on accessible Board, updated_at offset); few offsets force tie-breaks."""
    if draw(st.booleans()):
        embedded = draw(st.sampled_from([keyword, keyword.swapcase(), keyword.upper()]))
        title = draw(_FILLER) + embedded + draw(_FILLER)
    else:
        title = draw(st.text(alphabet=_ALPHABET, min_size=1, max_size=30))
    return title, draw(st.booleans()), draw(st.integers(0, 3))


_SCENARIO = _KEYWORD.flatmap(
    lambda keyword: st.tuples(
        st.just(keyword),
        st.one_of(
            st.lists(_card_spec(keyword), max_size=15),
            # Crosses the cap: more than SEARCH_PAGE_SIZE accessible matches.
            st.lists(
                _card_spec(keyword).map(lambda s: (s[0], True, s[2])),
                min_size=SEARCH_PAGE_SIZE + 1,
                max_size=SEARCH_PAGE_SIZE + 8,
            ).map(lambda specs: [(keyword + t, a, o) for t, a, o in specs]),
        ),
    )
)


# Feature: task-management-app, Property 16: Search result soundness, completeness, content, ordering, and cap  # noqa: E501
@_SETTINGS
@given(scenario=_SCENARIO)
def test_search_is_sound_complete_ordered_and_capped(
    db_session: Any,
    make_user: Callable[..., User],
    make_board: Callable[..., Board],
    make_column: Callable[..., Column],
    scenario: tuple[str, list[tuple[str, bool, int]]],
) -> None:
    keyword, specs = scenario
    # A fresh requester per example: only their Boards are searched, so data from
    # earlier examples (same rolled-back transaction) never leaks in.
    requester = make_user()
    stranger = make_user()
    own_board = make_board(admin=requester, name="Own")
    other_board = make_board(admin=stranger, name="Other")
    own_column = make_column(board=own_board, name="Own column")
    other_column = make_column(board=other_board, name="Other column")

    cards: list[tuple[Card, bool]] = []
    for title, accessible, offset in specs:
        board, column = (own_board, own_column) if accessible else (other_board, other_column)
        card = Card(
            column_id=column.id,
            board_id=board.id,
            title=title,
            created_by_id=stranger.id,
            order_index=len(cards),
            updated_at=_BASE_TIME + timedelta(seconds=offset),
        )
        cards.append((card, accessible))
    db_session.add_all([card for card, _ in cards])
    db_session.flush()

    result = search_cards_service(requester, {"q": keyword})["items"]

    matching = [
        card for card, accessible in cards if accessible and keyword.lower() in card.title.lower()
    ]
    expected = sorted(matching, key=lambda c: (c.updated_at, c.id), reverse=True)
    expected = expected[:SEARCH_PAGE_SIZE]

    # Soundness: literal case-insensitive substring, accessible Board only, no duplicates.
    ids = [item["id"] for item in result]
    assert len(set(ids)) == len(ids)
    assert len(result) <= SEARCH_PAGE_SIZE
    for item in result:
        assert keyword.lower() in item["title"].lower()
        assert item["board"] == {"id": own_board.id, "name": "Own"}

    # Completeness, ordering and cap: exactly the first SEARCH_PAGE_SIZE matches in order.
    assert ids == [c.id for c in expected]
    if not matching:
        assert result == []

    # Content: each result carries its Board and Column.
    for item in result:
        assert item["column"] == {"id": own_column.id, "name": "Own column"}

"""Schema verification against PostgreSQL (R2.3, R4.2, R4.7).

Tests that need real commits, row locks or Alembic use their own connections and
clean up afterwards, because the shared ``db_session`` fixture never really commits.
"""

import os
import uuid
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from flask import Flask
from flask_migrate import downgrade, upgrade
from marshmallow import validate
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from flask_app.app import create_app
from flask_app.common.exceptions import ValidationError
from flask_app.common.validation import BaseSchema, TrimmedStr, load_schema
from flask_app.extensions import db
from flask_app.models import Board, Card, Column, Team, TeamMembership, User

BACKEND_DIR = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------- helpers


def _seed_board_with_cards(
    session: Session, column_count: int = 3, card_count: int = 3
) -> tuple[Board, list[Column], list[Card]]:
    user = User(
        email=f"u-{uuid.uuid4().hex[:12]}@example.com",
        password_hash="$argon2id$placeholder",
        display_name="Schema Test",
    )
    session.add(user)
    session.flush()
    team = Team(name="Team")
    session.add(team)
    session.flush()
    session.add(TeamMembership(team_id=team.id, user_id=user.id, team_role="team_admin"))
    board = Board(team_id=team.id, name="Board")
    session.add(board)
    session.flush()
    columns = [Column(board_id=board.id, name=f"C{i}", order_index=i) for i in range(column_count)]
    session.add_all(columns)
    session.flush()
    cards = [
        Card(
            column_id=columns[0].id,
            board_id=board.id,
            title=f"Card {i}",
            created_by_id=user.id,
            order_index=i,
        )
        for i in range(card_count)
    ]
    session.add_all(cards)
    session.flush()
    return board, columns, cards


@pytest.fixture
def committed_session(app: Flask) -> Iterator[Callable[[], Session]]:
    """Factory for sessions that really commit; all tables are truncated afterwards."""
    opened: list[Session] = []

    def _open() -> Session:
        session = Session(bind=db.engine)
        opened.append(session)
        return session

    try:
        yield _open
    finally:
        for session in opened:
            session.rollback()
            session.close()
        names = ", ".join(f'"{t.name}"' for t in db.metadata.sorted_tables)
        with db.engine.begin() as conn:
            conn.execute(text(f"TRUNCATE {names} CASCADE"))


# ------------------------------------------------- deferrable order_index


def test_card_reindex_swap_and_shift_in_one_transaction(
    committed_session: Callable[[], Session],
) -> None:
    session = committed_session()
    _, _, cards = _seed_board_with_cards(session, card_count=4)
    session.commit()

    # swap two cards, then shift the rest by one (order 0..3 -> 1,0,3,2 style rotation)
    cards[0].order_index, cards[1].order_index = 1, 0
    cards[2].order_index, cards[3].order_index = 3, 2
    session.commit()

    order = [c.title for c in session.scalars(select(Card).order_by(Card.order_index)).all()]
    assert order == ["Card 1", "Card 0", "Card 3", "Card 2"]


def test_column_reindex_in_one_transaction(committed_session: Callable[[], Session]) -> None:
    session = committed_session()
    _, columns, _ = _seed_board_with_cards(session, column_count=3)
    session.commit()

    columns[0].order_index, columns[1].order_index, columns[2].order_index = 2, 0, 1
    session.commit()

    names = [c.name for c in session.scalars(select(Column).order_by(Column.order_index)).all()]
    assert names == ["C1", "C2", "C0"]


def test_duplicate_card_order_index_fails_at_commit(
    committed_session: Callable[[], Session],
) -> None:
    session = committed_session()
    _, _, cards = _seed_board_with_cards(session)
    session.commit()

    cards[1].order_index = cards[0].order_index
    session.flush()  # deferred: no error yet
    with pytest.raises(IntegrityError):
        session.commit()


def test_duplicate_column_order_index_fails_at_commit(
    committed_session: Callable[[], Session],
) -> None:
    session = committed_session()
    _, columns, _ = _seed_board_with_cards(session)
    session.commit()

    columns[1].order_index = columns[0].order_index
    session.flush()
    with pytest.raises(IntegrityError):
        session.commit()


# ------------------------------------------------------ Card updated_at


def test_unrelated_updates_do_not_change_card_updated_at(
    db_session: Any,
    make_card: Callable[..., Card],
    make_column: Callable[..., Column],
) -> None:
    column = make_column()
    card = make_card(column=column)
    other = make_card(column=column)
    stamp = datetime(2024, 1, 1, tzinfo=UTC)
    card.updated_at = stamp
    other.updated_at = stamp
    db_session.flush()

    card.description = "changed description"
    other.order_index = 5
    db_session.flush()
    db_session.expire_all()

    assert card.updated_at == stamp
    assert other.updated_at == stamp


# --------------------------------------------------------- row locking


def test_with_for_update_locks_column_row(
    committed_session: Callable[[], Session],
) -> None:
    setup = committed_session()
    _, columns, _ = _seed_board_with_cards(setup)
    column_id = columns[0].id
    setup.commit()
    setup.close()

    holder = committed_session()
    holder.execute(select(Column).where(Column.id == column_id).with_for_update()).scalar_one()

    contender = committed_session()
    contender.execute(text("SET lock_timeout = '2s'"))
    skipped = contender.scalars(
        select(Column).where(Column.id == column_id).with_for_update(skip_locked=True)
    ).all()
    assert skipped == []

    with pytest.raises(DBAPIError):
        contender.execute(
            select(Column).where(Column.id == column_id).with_for_update(nowait=True)
        ).scalar_one()
    contender.rollback()

    holder.rollback()  # releases the lock
    acquired = contender.scalars(
        select(Column).where(Column.id == column_id).with_for_update(nowait=True)
    ).all()
    assert len(acquired) == 1


# ---------------------------------------------------------- TrimmedStr


class _OneCharSchema(BaseSchema):
    value = TrimmedStr(required=True, validate=validate.Length(min=1, max=1))


def test_trimmed_str_trims_before_length_check() -> None:
    assert load_schema(_OneCharSchema(), {"value": "  a  "}) == {"value": "a"}


def test_trimmed_str_rejects_blank_for_min_length() -> None:
    with pytest.raises(ValidationError):
        load_schema(_OneCharSchema(), {"value": "   "})


def test_trimmed_str_rejects_too_long_after_trim() -> None:
    with pytest.raises(ValidationError):
        load_schema(_OneCharSchema(), {"value": " ab "})


# ------------------------------------------------- Alembic db.Uuid


@pytest.fixture
def migration_app() -> Iterator[Flask]:
    url = os.environ.get("MIGRATION_TEST_DATABASE_URL", "").strip()
    if not url:
        pytest.skip("MIGRATION_TEST_DATABASE_URL is not set")
    flask_app = create_app(
        {
            "APP_ENV": "test",
            "TESTING": True,
            "DEBUG": False,
            "SQLALCHEMY_DATABASE_URI": url,
            "JWT_SECRET_KEY": "test-secret-key-not-for-production-use",
            "COOKIE_SECURE": False,
            "ACCESS_TOKEN_MINUTES": 15,
            "REFRESH_TOKEN_DAYS": 7,
            "ACCESS_COOKIE_NAME": "access_token",
            "REFRESH_COOKIE_NAME": "refresh_token",
        }
    )
    with flask_app.app_context():
        _reset(url)
        try:
            yield flask_app
        finally:
            db.session.remove()
            _reset(url)


def _reset(_: str) -> None:
    db.metadata.drop_all(bind=db.engine)
    with db.engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))


def _uuid_columns(conn: Any) -> list[tuple[str, str, str]]:
    rows = conn.execute(
        text(
            "SELECT table_name, column_name, data_type FROM information_schema.columns "
            "WHERE table_schema = 'public' AND column_name = 'id' "
            "AND table_name <> 'alembic_version'"
        )
    ).all()
    return [(r[0], r[1], r[2]) for r in rows]


def test_uuid_columns_survive_alembic_upgrade_and_downgrade(migration_app: Flask) -> None:
    directory = str(BACKEND_DIR / "migrations")

    upgrade(directory=directory)
    with db.engine.connect() as conn:
        columns = _uuid_columns(conn)
        fk_types = (
            conn.execute(
                text(
                    "SELECT data_type FROM information_schema.columns "
                    "WHERE table_schema = 'public' AND table_name = 'cards' "
                    "AND column_name IN ('column_id', 'board_id', 'created_by_id')"
                )
            )
            .scalars()
            .all()
        )
    assert columns, "no tables were created by upgrade"
    assert all(data_type == "uuid" for _, _, data_type in columns), columns
    assert fk_types == ["uuid"] * 3 or set(fk_types) == {"uuid"}

    downgrade(directory=directory, revision="base")
    with db.engine.connect() as conn:
        remaining = (
            conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name <> 'alembic_version'"
                )
            )
            .scalars()
            .all()
        )
    assert remaining == []

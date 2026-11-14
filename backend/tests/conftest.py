"""Shared pytest fixtures: test app, rollback-per-test DB session, factories, clock."""

import os
import uuid
from collections.abc import Callable, Iterator
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from dotenv import load_dotenv
from flask import Flask
from sqlalchemy.orm import scoped_session, sessionmaker

from flask_app.app import create_app
from flask_app.extensions import db
from flask_app.models import (
    Board,
    BoardMembership,
    Card,
    Column,
    Team,
    TeamMembership,
    User,
)

load_dotenv()

PLACEHOLDER_HASH = "$argon2id$placeholder-not-a-real-hash"


@pytest.fixture(scope="session")
def app() -> Iterator[Flask]:
    """Flask app bound to TEST_DATABASE_URL; schema is created once per session."""
    url = os.environ.get("TEST_DATABASE_URL", "").strip()
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set")
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
        db.drop_all()
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def db_session(app: Flask) -> Iterator[Any]:
    """Session inside an outer transaction that is rolled back after each test.

    Commits inside services only release a SAVEPOINT, so nothing persists.
    """
    with app.app_context():
        connection = db.engine.connect()
        outer = connection.begin()
        original = db.session
        test_session = scoped_session(
            sessionmaker(bind=connection, join_transaction_mode="create_savepoint")
        )
        db.session = test_session  # type: ignore[assignment]
        try:
            yield test_session
        finally:
            test_session.remove()
            db.session = original
            outer.rollback()
            connection.close()


@pytest.fixture
def client(app: Flask, db_session: Any) -> Any:
    return app.test_client()


class FakeClock:
    """Controllable replacement for the current time used by ``utc_now``."""

    def __init__(self, start: datetime) -> None:
        self.now = start

    def set(self, value: datetime) -> None:
        self.now = value

    def advance(self, **kwargs: float) -> datetime:
        self.now = self.now + timedelta(**kwargs)
        return self.now


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> FakeClock:
    """Freeze and control ``utc_now`` everywhere, including model column defaults.

    ``utc_now`` is imported by name in many modules and captured as a column
    default, so patching the function itself would miss those references.
    Instead the ``datetime`` class it calls is replaced.
    """
    fake = FakeClock(datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC))

    class _FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz: Any = None) -> _FrozenDatetime:
            value = fake.now if tz is None else fake.now.astimezone(tz)
            return cls.fromtimestamp(value.timestamp(), tz=value.tzinfo)

    monkeypatch.setattr("flask_app.common.time.datetime", _FrozenDatetime)
    return fake


@pytest.fixture
def make_user(db_session: Any) -> Callable[..., User]:
    def _make(
        email: str | None = None,
        display_name: str = "Test User",
        password_hash: str = PLACEHOLDER_HASH,
        **extra: Any,
    ) -> User:
        user = User(
            email=email or f"user-{uuid.uuid4().hex[:12]}@example.com",
            password_hash=password_hash,
            display_name=display_name,
            **extra,
        )
        db_session.add(user)
        db_session.flush()
        return user

    return _make


@pytest.fixture
def make_team(db_session: Any, make_user: Callable[..., User]) -> Callable[..., Team]:
    def _make(name: str = "Team", admin: User | None = None) -> Team:
        team = Team(name=name)
        db_session.add(team)
        db_session.flush()
        owner = admin or make_user()
        db_session.add(TeamMembership(team_id=team.id, user_id=owner.id, team_role="team_admin"))
        db_session.flush()
        return team

    return _make


@pytest.fixture
def make_board(
    db_session: Any, make_team: Callable[..., Team], make_user: Callable[..., User]
) -> Callable[..., Board]:
    def _make(
        team: Team | None = None,
        admin: User | None = None,
        name: str = "Board",
        **extra: Any,
    ) -> Board:
        owner = admin or make_user()
        board_team = team or make_team(admin=owner)
        board = Board(team_id=board_team.id, name=name, **extra)
        db_session.add(board)
        db_session.flush()
        db_session.add(BoardMembership(board_id=board.id, user_id=owner.id, role="admin"))
        db_session.flush()
        return board

    return _make


@pytest.fixture
def make_column(db_session: Any, make_board: Callable[..., Board]) -> Callable[..., Column]:
    def _make(
        board: Board | None = None, name: str = "To Do", order_index: int | None = None
    ) -> Column:
        target = board or make_board()
        if order_index is None:
            order_index = db_session.query(Column).filter(Column.board_id == target.id).count()
        column = Column(board_id=target.id, name=name, order_index=order_index)
        db_session.add(column)
        db_session.flush()
        return column

    return _make


@pytest.fixture
def make_card(
    db_session: Any, make_column: Callable[..., Column], make_user: Callable[..., User]
) -> Callable[..., Card]:
    def _make(
        column: Column | None = None,
        title: str = "Card",
        created_by: User | None = None,
        order_index: int | None = None,
        assignee: User | None = None,
        due_date: date | None = None,
        **extra: Any,
    ) -> Card:
        target = column or make_column()
        author = created_by or make_user()
        if order_index is None:
            order_index = db_session.query(Card).filter(Card.column_id == target.id).count()
        card = Card(
            column_id=target.id,
            board_id=target.board_id,
            title=title,
            created_by_id=author.id,
            assignee_id=assignee.id if assignee else None,
            due_date=due_date,
            order_index=order_index,
            **extra,
        )
        db_session.add(card)
        db_session.flush()
        return card

    return _make

"""Demo and E2E seed data. Idempotent. Run from backend/: python -m scripts.seed"""

from datetime import date, timedelta
from typing import Any

from sqlalchemy import select

from flask_app.auth.service import hash_password
from flask_app.boards.service import DEFAULT_COLUMNS
from flask_app.common.time import utc_now
from flask_app.extensions import db
from flask_app.models import (
    Board,
    BoardMembership,
    Card,
    Column,
    Comment,
    InvitationLink,
    Team,
    TeamMembership,
    User,
)

DEMO_PASSWORD = "Password123!"
ADMIN_EMAIL = "admin@example.com"
MEMBER_EMAIL = "member@example.com"
OUTSIDER_EMAIL = "outsider@example.com"
TEAM_NAME = "Demo Team"
BOARD_NAME = "Demo Board"
INVITATION_TOKEN = "demo-invitation-token-for-e2e-0000000000000001"

_CARDS: dict[str, list[str]] = {
    "To Do": ["Write project brief", "Set up CI"],
    "Doing": ["Design login page"],
    "Done": ["Create repository"],
}


def _get_or_create_user(email: str, display_name: str) -> User:
    user = db.session.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(
            email=email, display_name=display_name, password_hash=hash_password(DEMO_PASSWORD)
        )
        db.session.add(user)
        db.session.flush()
    return user


def _ensure_team_membership(team: Team, user: User, role: str) -> None:
    exists = db.session.scalar(
        select(TeamMembership).where(
            TeamMembership.team_id == team.id, TeamMembership.user_id == user.id
        )
    )
    if exists is None:
        db.session.add(TeamMembership(team_id=team.id, user_id=user.id, team_role=role))


def _ensure_board_membership(board: Board, user: User, role: str) -> None:
    exists = db.session.scalar(
        select(BoardMembership).where(
            BoardMembership.board_id == board.id, BoardMembership.user_id == user.id
        )
    )
    if exists is None:
        db.session.add(BoardMembership(board_id=board.id, user_id=user.id, role=role))


def seed_data() -> dict[str, Any]:
    """Create the seed rows that are missing and commit once. Safe to run repeatedly."""
    admin = _get_or_create_user(ADMIN_EMAIL, "Demo Admin")
    member = _get_or_create_user(MEMBER_EMAIL, "Demo Member")
    _get_or_create_user(OUTSIDER_EMAIL, "Demo Outsider")

    team = db.session.scalar(select(Team).where(Team.name == TEAM_NAME))
    if team is None:
        team = Team(name=TEAM_NAME)
        db.session.add(team)
        db.session.flush()
    _ensure_team_membership(team, admin, "team_admin")
    _ensure_team_membership(team, member, "team_regular")

    board = db.session.scalar(
        select(Board).where(Board.team_id == team.id, Board.name == BOARD_NAME)
    )
    if board is None:
        board = Board(team_id=team.id, name=BOARD_NAME, description="Seeded demo board")
        db.session.add(board)
        db.session.flush()
        columns = {}
        for index, name in enumerate(DEFAULT_COLUMNS):
            column = Column(board_id=board.id, name=name, order_index=index)
            db.session.add(column)
            columns[name] = column
        db.session.flush()
        now = utc_now()
        first_card: Card | None = None
        for column_name, titles in _CARDS.items():
            for index, title in enumerate(titles):
                card = Card(
                    column_id=columns[column_name].id,
                    board_id=board.id,
                    title=title,
                    created_by_id=admin.id,
                    assignee_id=member.id if index == 0 else None,
                    due_date=date.today() + timedelta(days=7) if index == 0 else None,
                    order_index=index,
                    created_at=now,
                    updated_at=now,
                )
                db.session.add(card)
                first_card = first_card or card
        db.session.flush()
        if first_card is not None:
            root = Comment(card_id=first_card.id, author_id=admin.id, body="Kick-off comment")
            db.session.add(root)
            db.session.flush()
            db.session.add(
                Comment(
                    card_id=first_card.id,
                    author_id=member.id,
                    parent_comment_id=root.id,
                    body=f"On it, @[{admin.id}]",
                )
            )
    _ensure_board_membership(board, admin, "admin")
    _ensure_board_membership(board, member, "member")

    link = db.session.scalar(select(InvitationLink).where(InvitationLink.token == INVITATION_TOKEN))
    if link is None:
        db.session.add(
            InvitationLink(
                board_id=board.id, token=INVITATION_TOKEN, status="active", created_by_id=admin.id
            )
        )
    db.session.commit()
    return {"team_id": team.id, "board_id": board.id}


def main() -> None:
    from flask_app.app import create_app

    app = create_app()
    with app.app_context():
        seed_data()
    print("Seed complete.")  # noqa: T201


if __name__ == "__main__":
    main()

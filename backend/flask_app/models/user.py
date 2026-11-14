from flask_app.extensions import db
from flask_app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(255), nullable=False)
    failed_login_attempts = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime(timezone=True), nullable=True)

    refresh_tokens = db.relationship(
        "RefreshToken",
        back_populates="user",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    team_memberships = db.relationship(
        "TeamMembership",
        back_populates="user",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    board_memberships = db.relationship(
        "BoardMembership",
        back_populates="user",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    created_team_join_links = db.relationship(
        "TeamJoinLink",
        back_populates="created_by",
        lazy="select",
    )

from flask_app.extensions import db
from flask_app.models.base import BaseModel


class Board(BaseModel):
    __tablename__ = "boards"
    __table_args__ = (
        db.CheckConstraint("visibility IN ('private', 'team')", name="visibility"),
        db.CheckConstraint("status IN ('active', 'archived')", name="status"),
    )

    team_id = db.Column(
        db.Uuid,
        db.ForeignKey("teams.id"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    visibility = db.Column(db.String(50), nullable=False, default="private")
    status = db.Column(db.String(50), nullable=False, default="active")

    team = db.relationship("Team", back_populates="boards", lazy="select")
    memberships = db.relationship(
        "BoardMembership",
        back_populates="board",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    columns = db.relationship(
        "Column",
        back_populates="board",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Column.order_index",
    )
    cards = db.relationship(
        "Card",
        back_populates="board",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    invitation_links = db.relationship(
        "InvitationLink",
        back_populates="board",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    activity_entries = db.relationship(
        "ActivityEntry",
        back_populates="board",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    notifications = db.relationship(
        "Notification",
        back_populates="board",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

from flask_app.common.time import utc_now
from flask_app.extensions import db
from flask_app.models.base import BaseModel


class Card(BaseModel):
    __tablename__ = "cards"
    __table_args__ = (
        db.UniqueConstraint("column_id", "order_index", deferrable=True, initially="DEFERRED"),
        db.Index("ix_cards_board_id_lower_title", "board_id", db.text("lower(title)")),
        db.Index(
            "ix_cards_board_id_updated_at_id",
            "board_id",
            db.text("updated_at DESC"),
            db.text("id DESC"),
        ),
    )

    # Card-specific: no onupdate, so reindexing never bumps updated_at.
    # Card_Service sets it explicitly.
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    column_id = db.Column(
        db.Uuid,
        db.ForeignKey("columns.id", ondelete="CASCADE"),
        nullable=False,
    )
    board_id = db.Column(
        db.Uuid,
        db.ForeignKey("boards.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    assignee_id = db.Column(db.Uuid, db.ForeignKey("users.id"), nullable=True, index=True)
    due_date = db.Column(db.Date, nullable=True)
    created_by_id = db.Column(db.Uuid, db.ForeignKey("users.id"), nullable=False, index=True)
    order_index = db.Column(db.Integer, nullable=False)
    version = db.Column(db.Integer, nullable=False, default=1)

    column = db.relationship("Column", back_populates="cards", lazy="select")
    board = db.relationship("Board", back_populates="cards", lazy="select")
    assignee = db.relationship("User", foreign_keys=[assignee_id], lazy="select")
    created_by = db.relationship("User", foreign_keys=[created_by_id], lazy="select")
    comments = db.relationship(
        "Comment",
        back_populates="card",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    checklist_items = db.relationship(
        "ChecklistItem",
        back_populates="card",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="(ChecklistItem.order_index, ChecklistItem.id)",
    )
    attachments = db.relationship(
        "Attachment",
        back_populates="card",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="(Attachment.created_at, Attachment.id)",
    )

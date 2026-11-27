from flask_app.extensions import db
from flask_app.models.base import BaseModel

EVENT_TYPES = (
    "card_created",
    "card_updated",
    "card_moved",
    "card_deleted",
    "comment_created",
    "comment_edited",
    "comment_deleted",
    "column_created",
    "column_deleted",
    "member_joined",
    "member_removed",
    "attachment_added",
    "attachment_deleted",
)


class ActivityEntry(BaseModel):
    __tablename__ = "activity_entries"
    __table_args__ = (
        db.CheckConstraint(
            "event_type IN (" + ", ".join(f"'{e}'" for e in EVENT_TYPES) + ")",
            name="event_type",
        ),
        db.Index(
            "ix_activity_entries_board_id_created_at_id",
            "board_id",
            db.text("created_at DESC"),
            db.text("id DESC"),
        ),
    )

    board_id = db.Column(
        db.Uuid,
        db.ForeignKey("boards.id", ondelete="CASCADE"),
        nullable=False,
    )
    actor_id = db.Column(db.Uuid, db.ForeignKey("users.id"), nullable=False, index=True)
    event_type = db.Column(db.String(50), nullable=False)
    # Deliberately not foreign keys: the targets may already be deleted.
    resource_id = db.Column(db.Uuid, nullable=False)
    secondary_resource_id = db.Column(db.Uuid, nullable=True)
    # Snapshot of the names shown in the activity sentence; NULL for older entries.
    details = db.Column(db.JSON, nullable=True)

    board = db.relationship("Board", back_populates="activity_entries", lazy="select")
    actor = db.relationship("User", lazy="select")

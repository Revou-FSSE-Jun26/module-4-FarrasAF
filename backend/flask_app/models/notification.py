from flask_app.extensions import db
from flask_app.models.base import BaseModel


class Notification(BaseModel):
    __tablename__ = "notifications"
    __table_args__ = (
        db.UniqueConstraint("recipient_id", "comment_id"),
        db.CheckConstraint("status IN ('unread', 'read')", name="status"),
        db.Index(
            "ix_notifications_recipient_id_created_at_id",
            "recipient_id",
            db.text("created_at DESC"),
            db.text("id DESC"),
        ),
        db.Index(
            "ix_notifications_recipient_id_created_at_id_unread",
            "recipient_id",
            db.text("created_at DESC"),
            db.text("id DESC"),
            postgresql_where=db.text("status = 'unread'"),
        ),
    )

    recipient_id = db.Column(
        db.Uuid,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    comment_id = db.Column(
        db.Uuid,
        db.ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    board_id = db.Column(
        db.Uuid,
        db.ForeignKey("boards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = db.Column(db.String(50), nullable=False, default="unread")

    recipient = db.relationship("User", lazy="select")
    comment = db.relationship("Comment", back_populates="notifications", lazy="select")
    board = db.relationship("Board", back_populates="notifications", lazy="select")

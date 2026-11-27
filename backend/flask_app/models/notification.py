from flask_app.extensions import db
from flask_app.models.base import BaseModel


class Notification(BaseModel):
    __tablename__ = "notifications"
    __table_args__ = (
        db.UniqueConstraint("recipient_id", "comment_id"),
        db.CheckConstraint("status IN ('unread', 'read')", name="status"),
        db.CheckConstraint("type IN ('comment_mention', 'card_assigned')", name="type"),
        db.CheckConstraint(
            "(type = 'comment_mention' AND comment_id IS NOT NULL)"
            " OR (type = 'card_assigned' AND card_id IS NOT NULL)",
            name="type_target",
        ),
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
    type = db.Column(db.String(50), nullable=False, default="comment_mention")
    comment_id = db.Column(
        db.Uuid,
        db.ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    card_id = db.Column(
        db.Uuid,
        db.ForeignKey("cards.id", ondelete="CASCADE"),
        nullable=True,
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
    card = db.relationship("Card", back_populates="notifications", lazy="select")
    board = db.relationship("Board", back_populates="notifications", lazy="select")

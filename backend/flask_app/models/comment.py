from flask_app.extensions import db
from flask_app.models.base import BaseModel


class Comment(BaseModel):
    __tablename__ = "comments"

    card_id = db.Column(
        db.Uuid,
        db.ForeignKey("cards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_id = db.Column(db.Uuid, db.ForeignKey("users.id"), nullable=False, index=True)
    parent_comment_id = db.Column(
        db.Uuid,
        db.ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    body = db.Column(db.Text, nullable=False)
    edited_at = db.Column(db.DateTime(timezone=True), nullable=True)
    version = db.Column(db.Integer, nullable=False, default=1)

    card = db.relationship("Card", back_populates="comments", lazy="select")
    author = db.relationship("User", lazy="select")
    parent = db.relationship(
        "Comment",
        back_populates="replies",
        remote_side="Comment.id",
        lazy="select",
    )
    replies = db.relationship(
        "Comment",
        back_populates="parent",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    notifications = db.relationship(
        "Notification",
        back_populates="comment",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

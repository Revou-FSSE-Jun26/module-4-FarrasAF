from flask_app.extensions import db
from flask_app.models.base import BaseModel


class BoardMembership(BaseModel):
    __tablename__ = "board_memberships"
    __table_args__ = (
        db.UniqueConstraint("board_id", "user_id"),
        db.CheckConstraint("role IN ('member', 'admin')", name="role"),
    )

    board_id = db.Column(
        db.Uuid,
        db.ForeignKey("boards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(
        db.Uuid,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = db.Column(db.String(50), nullable=False)

    board = db.relationship("Board", back_populates="memberships", lazy="select")
    user = db.relationship("User", back_populates="board_memberships", lazy="select")

from flask_app.extensions import db
from flask_app.models.base import BaseModel


class InvitationLink(BaseModel):
    __tablename__ = "invitation_links"
    __table_args__ = (db.CheckConstraint("status IN ('active', 'inactive')", name="status"),)

    board_id = db.Column(
        db.Uuid,
        db.ForeignKey("boards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token = db.Column(db.String(255), nullable=False, unique=True)
    status = db.Column(db.String(50), nullable=False, default="active")
    created_by_id = db.Column(db.Uuid, db.ForeignKey("users.id"), nullable=False, index=True)

    board = db.relationship("Board", back_populates="invitation_links", lazy="select")
    created_by = db.relationship("User", lazy="select")

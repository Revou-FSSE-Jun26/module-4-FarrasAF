from flask_app.extensions import db
from flask_app.models.base import BaseModel


class TeamJoinLink(BaseModel):
    __tablename__ = "team_join_links"
    __table_args__ = (db.CheckConstraint("status IN ('active', 'inactive')", name="status"),)

    team_id = db.Column(
        db.Uuid,
        db.ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token = db.Column(db.String(255), nullable=False, unique=True)
    status = db.Column(db.String(50), nullable=False, default="active")
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    created_by_id = db.Column(
        db.Uuid,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    team = db.relationship("Team", back_populates="join_links", lazy="select")
    created_by = db.relationship("User", back_populates="created_team_join_links", lazy="select")

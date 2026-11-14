from flask_app.extensions import db
from flask_app.models.base import BaseModel


class TeamMembership(BaseModel):
    __tablename__ = "team_memberships"
    __table_args__ = (
        db.UniqueConstraint("team_id", "user_id"),
        db.CheckConstraint("team_role IN ('team_admin', 'team_regular')", name="team_role"),
    )

    team_id = db.Column(
        db.Uuid,
        db.ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(
        db.Uuid,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    team_role = db.Column(db.String(50), nullable=False)

    team = db.relationship("Team", back_populates="memberships", lazy="select")
    user = db.relationship("User", back_populates="team_memberships", lazy="select")

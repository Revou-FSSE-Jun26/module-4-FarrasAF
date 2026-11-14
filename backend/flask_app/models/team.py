from flask_app.extensions import db
from flask_app.models.base import BaseModel


class Team(BaseModel):
    __tablename__ = "teams"

    name = db.Column(db.String(255), nullable=False)

    memberships = db.relationship(
        "TeamMembership",
        back_populates="team",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    boards = db.relationship("Board", back_populates="team", lazy="select")
    join_links = db.relationship(
        "TeamJoinLink",
        back_populates="team",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

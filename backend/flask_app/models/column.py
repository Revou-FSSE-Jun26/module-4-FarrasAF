from flask_app.extensions import db
from flask_app.models.base import BaseModel


class Column(BaseModel):
    __tablename__ = "columns"
    __table_args__ = (
        db.UniqueConstraint("board_id", "order_index", deferrable=True, initially="DEFERRED"),
    )

    board_id = db.Column(
        db.Uuid,
        db.ForeignKey("boards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(255), nullable=False)
    order_index = db.Column(db.Integer, nullable=False)

    board = db.relationship("Board", back_populates="columns", lazy="select")
    cards = db.relationship(
        "Card",
        back_populates="column",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Card.order_index",
    )

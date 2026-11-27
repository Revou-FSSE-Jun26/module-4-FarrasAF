from flask_app.extensions import db
from flask_app.models.base import BaseModel


class ChecklistItem(BaseModel):
    """One to-do item of a Card's single to-do list."""

    __tablename__ = "checklist_items"

    card_id = db.Column(
        db.Uuid,
        db.ForeignKey("cards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text = db.Column(db.String(255), nullable=False)
    is_done = db.Column(db.Boolean, nullable=False, default=False)
    # New items go last; items are never reordered, so a gap after a delete is harmless.
    order_index = db.Column(db.Integer, nullable=False)

    card = db.relationship("Card", back_populates="checklist_items", lazy="select")

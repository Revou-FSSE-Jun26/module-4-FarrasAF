from flask_app.extensions import db
from flask_app.models.base import BaseModel

RESOURCE_TYPES = ("image", "raw")


class Attachment(BaseModel):
    """A file attached to a Card, stored in Cloudinary."""

    __tablename__ = "attachments"
    __table_args__ = (
        db.CheckConstraint(
            "resource_type IN (" + ", ".join(f"'{t}'" for t in RESOURCE_TYPES) + ")",
            name="resource_type",
        ),
    )

    card_id = db.Column(
        db.Uuid,
        db.ForeignKey("cards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uploaded_by_id = db.Column(db.Uuid, db.ForeignKey("users.id"), nullable=False, index=True)
    file_name = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(255), nullable=False)
    size_bytes = db.Column(db.Integer, nullable=False)
    url = db.Column(db.Text, nullable=False)
    # Cloudinary identifier, needed to delete the file.
    public_id = db.Column(db.String(255), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)

    card = db.relationship("Card", back_populates="attachments", lazy="select")
    # Joined so listing a Card's Attachments needs no extra query per uploader.
    uploaded_by = db.relationship("User", lazy="joined")

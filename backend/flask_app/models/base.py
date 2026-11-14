import uuid

from flask_app.common.time import utc_now
from flask_app.extensions import db


class BaseModel(db.Model):  # type: ignore[name-defined,misc]
    """Abstract base: exactly id, created_at, updated_at, deleted_at."""

    __abstract__ = True

    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)

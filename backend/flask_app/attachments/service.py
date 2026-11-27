"""Card attachments stored in Cloudinary (R22)."""

import posixpath
import secrets
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from flask import current_app
from sqlalchemy import func, select

from flask_app.access.rbac import get_board_role
from flask_app.activity.service import record_activity
from flask_app.common.exceptions import AuthorizationError, NotFoundError, ValidationError
from flask_app.common.serialization import UploadedFile
from flask_app.common.storage import StoredFile, delete_file, upload_file
from flask_app.extensions import db
from flask_app.models import Attachment, Card, User

MAX_ATTACHMENT_BYTES = 5 * 1024 * 1024
MAX_ATTACHMENTS_PER_CARD = 5
MAX_FILE_NAME_LENGTH = 255
IMAGE_EXTENSIONS = frozenset({"jpg", "jpeg", "png", "webp"})
RAW_EXTENSIONS = frozenset({"pdf", "docx", "xlsx", "pptx", "txt", "csv"})
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | RAW_EXTENSIONS
_ADMIN = "admin"


@dataclass(frozen=True)
class AssetRef:
    """The Cloudinary identity of a stored file."""

    public_id: str
    resource_type: str


def file_extension(file_name: str) -> str:
    """The lower-case extension without the dot, or "" when there is none."""
    return posixpath.splitext(file_name)[1].lstrip(".").lower()


def validate_upload(file_name: str, size_bytes: int) -> str:
    """Check an upload against the R22 limits and return the cleaned file name.

    Pure function: no database and no Cloudinary access.
    """
    # Browsers send a bare name, but some clients send a path; keep the last part.
    clean = posixpath.basename(file_name.replace("\\", "/")).strip()
    if not clean:
        raise ValidationError("The file name is required", field="file")
    if len(clean) > MAX_FILE_NAME_LENGTH:
        raise ValidationError(
            f"The file name must be at most {MAX_FILE_NAME_LENGTH} characters", field="file"
        )
    if file_extension(clean) not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise ValidationError(f"File type not allowed. Allowed types: {allowed}", field="file")
    if size_bytes <= 0:
        raise ValidationError("The file is empty", field="file")
    if size_bytes > MAX_ATTACHMENT_BYTES:
        limit_mb = MAX_ATTACHMENT_BYTES // (1024 * 1024)
        raise ValidationError(f"The file is larger than {limit_mb} MB", field="file")
    return clean


def resource_type_for(extension: str) -> str:
    return "image" if extension in IMAGE_EXTENSIONS else "raw"


def build_download_url(url: str, resource_type: str) -> str:
    """Images get the `fl_attachment` flag so the browser saves them instead of showing them."""
    if resource_type == "image":
        return url.replace("/image/upload/", "/image/upload/fl_attachment/", 1)
    return url


def attachment_dict(attachment: Attachment) -> dict[str, Any]:
    return {
        "id": attachment.id,
        "card_id": attachment.card_id,
        "file_name": attachment.file_name,
        "content_type": attachment.content_type,
        "size_bytes": attachment.size_bytes,
        "url": attachment.url,
        "download_url": build_download_url(attachment.url, attachment.resource_type),
        "uploaded_by": {
            "id": attachment.uploaded_by.id,
            "display_name": attachment.uploaded_by.display_name,
        },
        "created_at": attachment.created_at,
    }


def destroy_assets(refs: list[AssetRef]) -> None:
    """Best-effort removal of files from Cloudinary; a failure is logged and ignored (R22.8)."""
    for ref in refs:
        try:
            delete_file(ref.public_id, ref.resource_type)
        except Exception as exc:
            current_app.logger.warning(
                "Cloudinary delete failed (%s) for a stored attachment", type(exc).__name__
            )


def card_asset_refs(card_id: UUID) -> list[AssetRef]:
    rows = db.session.execute(
        select(Attachment.public_id, Attachment.resource_type).where(Attachment.card_id == card_id)
    ).all()
    return [AssetRef(public_id, resource_type) for public_id, resource_type in rows]


def board_asset_refs(board_id: UUID) -> list[AssetRef]:
    rows = db.session.execute(
        select(Attachment.public_id, Attachment.resource_type)
        .join(Card, Card.id == Attachment.card_id)
        .where(Card.board_id == board_id)
    ).all()
    return [AssetRef(public_id, resource_type) for public_id, resource_type in rows]


def _store(card_id: UUID, extension: str, data: bytes) -> StoredFile:
    resource_type = resource_type_for(extension)
    # Raw files keep their extension in the public id so the URL ends with it.
    public_id = secrets.token_hex(16) + ("" if resource_type == "image" else f".{extension}")
    try:
        return upload_file(
            data,
            folder=f"task-management-app/cards/{card_id}",
            public_id=public_id,
            resource_type=resource_type,
        )
    except Exception as exc:
        current_app.logger.error("Cloudinary upload failed (%s)", type(exc).__name__)
        # A new error without the chain, so no Cloudinary details reach the logs or the client.
        raise RuntimeError("Attachment storage failed") from None


def upload_attachment_service(card_id: UUID, uploaded: UploadedFile, user: User) -> dict[str, Any]:
    """Store one file in Cloudinary and save its Attachment. Does not touch the Card's version."""
    file_name = validate_upload(uploaded.file_name, len(uploaded.data))
    # Lock the Card row so two concurrent uploads cannot pass the count limit together.
    card = db.session.scalar(select(Card).where(Card.id == card_id).with_for_update())
    if card is None:
        raise NotFoundError("Card not found")
    count = db.session.scalar(
        select(func.count()).select_from(Attachment).where(Attachment.card_id == card_id)
    )
    if (count or 0) >= MAX_ATTACHMENTS_PER_CARD:
        raise ValidationError(
            f"A Card can have at most {MAX_ATTACHMENTS_PER_CARD} attachments", field="file"
        )
    stored = _store(card_id, file_extension(file_name), uploaded.data)
    try:
        attachment = Attachment(
            card_id=card_id,
            uploaded_by_id=user.id,
            file_name=file_name,
            content_type=uploaded.content_type[:255],
            size_bytes=len(uploaded.data),
            url=stored.url,
            public_id=stored.public_id,
            resource_type=stored.resource_type,
        )
        db.session.add(attachment)
        db.session.flush()
        record_activity(
            card.board_id,
            user.id,
            "attachment_added",
            attachment.id,
            card.id,
            details={"card_title": card.title, "file_name": file_name},
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        # No record was saved, so the stored file would be an orphan (R22.14).
        destroy_assets([AssetRef(stored.public_id, stored.resource_type)])
        raise
    return attachment_dict(attachment)


def delete_attachment_service(attachment_id: UUID, user: User) -> None:
    """Delete an Attachment; only its uploader or a Board Admin may do so (R22.8, R22.9)."""
    attachment = db.session.get(Attachment, attachment_id)
    if attachment is None:
        raise NotFoundError("Attachment not found")
    card = db.session.get(Card, attachment.card_id)
    if card is None:
        raise NotFoundError("Card not found")
    if attachment.uploaded_by_id != user.id and get_board_role(card.board_id, user.id) != _ADMIN:
        raise AuthorizationError("Only the uploader or an Admin can delete this attachment")
    ref = AssetRef(attachment.public_id, attachment.resource_type)
    record_activity(
        card.board_id,
        user.id,
        "attachment_deleted",
        attachment.id,
        card.id,
        details={"card_title": card.title, "file_name": attachment.file_name},
    )
    db.session.delete(attachment)
    db.session.commit()
    destroy_assets([ref])

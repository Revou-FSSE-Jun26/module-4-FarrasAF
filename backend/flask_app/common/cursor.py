"""Opaque keyset cursor codec for (created_at, id) pagination."""

import base64
import binascii
import json
import re
import uuid
from datetime import UTC, datetime

from flask_app.common.exceptions import ValidationError

_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_INVALID = "Invalid cursor"


def encode_cursor(created_at: datetime, id: uuid.UUID) -> str:
    """Encode a position as a URL-safe, unpadded base64 string.

    A naive datetime is treated as UTC; aware ones are converted to UTC.
    """
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    else:
        created_at = created_at.astimezone(UTC)
    payload = json.dumps([created_at.isoformat(), str(id)], separators=(",", ":"))
    return base64.urlsafe_b64encode(payload.encode("utf-8")).rstrip(b"=").decode("ascii")


def decode_cursor(token: str) -> tuple[datetime, uuid.UUID]:
    """Decode a cursor into (UTC-aware created_at, id); raise ValidationError if malformed."""
    if not isinstance(token, str) or not _TOKEN_RE.fullmatch(token):
        raise ValidationError(_INVALID, field="cursor")
    try:
        padded = token + "=" * (-len(token) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))
        if not (
            isinstance(data, list)
            and len(data) == 2
            and isinstance(data[0], str)
            and isinstance(data[1], str)
        ):
            raise ValueError("bad shape")
        created_at = datetime.fromisoformat(data[0])
        if created_at.tzinfo is None:
            raise ValueError("naive timestamp")
        item_id = uuid.UUID(data[1])
    except binascii.Error, ValueError, UnicodeDecodeError, RecursionError:
        raise ValidationError(_INVALID, field="cursor") from None
    return created_at.astimezone(UTC), item_id

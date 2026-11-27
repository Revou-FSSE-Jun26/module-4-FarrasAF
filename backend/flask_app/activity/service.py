from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from flask_app.common.pagination import ACTIVITY_PAGE_SIZE
from flask_app.extensions import db
from flask_app.models import ActivityEntry
from flask_app.models.activity_entry import EVENT_TYPES

# Keeps page * page size inside PostgreSQL's bigint OFFSET range.
_MAX_PAGE = 10**12


def record_activity(
    board_id: UUID,
    actor_id: UUID,
    event_type: str,
    resource_id: UUID,
    secondary_resource_id: UUID | None = None,
    details: dict[str, str] | None = None,
) -> ActivityEntry:
    """Add an Activity_Entry to the session. Never commits; the caller owns the transaction.

    `details` is a snapshot of the names shown in the activity sentence (Card title,
    Column names, member name), taken now because the targets may be deleted later.
    """
    if event_type not in EVENT_TYPES:
        raise ValueError(f"Unknown activity event type: {event_type}")
    entry = ActivityEntry(
        board_id=board_id,
        actor_id=actor_id,
        event_type=event_type,
        resource_id=resource_id,
        secondary_resource_id=secondary_resource_id,
        details=details,
    )
    db.session.add(entry)
    return entry


def _entry_to_dict(entry: ActivityEntry) -> dict[str, Any]:
    return {
        "id": entry.id,
        "event_type": entry.event_type,
        "created_at": entry.created_at,
        "actor": {"id": entry.actor.id, "display_name": entry.actor.display_name},
        "resource_id": entry.resource_id,
        "secondary_resource_id": entry.secondary_resource_id,
        "details": entry.details,
    }


def list_activity_service(board_id: UUID, payload: dict[str, Any]) -> dict[str, Any]:
    """One zero-based page of the Board's activity, newest first; invalid pages are empty."""
    page: int = payload.get("page", 0)
    items: list[dict[str, Any]] = []
    if 0 <= page <= _MAX_PAGE:
        query = (
            select(ActivityEntry)
            .options(joinedload(ActivityEntry.actor))  # type: ignore[arg-type]
            .where(ActivityEntry.board_id == board_id)
            .order_by(ActivityEntry.created_at.desc(), ActivityEntry.id.desc())
            .limit(ACTIVITY_PAGE_SIZE)
            .offset(page * ACTIVITY_PAGE_SIZE)
        )
        items = [_entry_to_dict(e) for e in db.session.scalars(query).all()]
    return {"items": items, "page": page, "page_size": ACTIVITY_PAGE_SIZE}

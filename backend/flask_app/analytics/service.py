from collections.abc import Iterable
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import func, select

from flask_app.extensions import db
from flask_app.models import ActivityEntry, Card, Column

DONE_COLUMN_NAME = "Done"


def compute_completion_rate(column_counts: Iterable[tuple[str, int]]) -> float:
    """Cards in Columns named exactly "Done" divided by all Cards, in [0.0, 1.0].

    Pure function: returns 0.0 when there are no Cards or no "Done" Column.
    """
    pairs = list(column_counts)
    total = sum(count for _, count in pairs)
    if total <= 0:
        return 0.0
    done = sum(count for name, count in pairs if name == DONE_COLUMN_NAME)
    return min(1.0, max(0.0, done / total))


def get_analytics_service(board_id: UUID) -> dict[str, Any]:
    """Totals, per-Column counts, completion rate and activity by UTC day for a Board."""
    column_rows = db.session.execute(
        select(Column.id, Column.name, func.count(Card.id))
        .outerjoin(Card, Card.column_id == Column.id)
        .where(Column.board_id == board_id)
        .group_by(Column.id, Column.name, Column.order_index)
        .order_by(Column.order_index)
    ).all()
    per_column = [{"column_id": cid, "count": int(count)} for cid, _, count in column_rows]

    day = func.date(func.timezone("UTC", ActivityEntry.created_at))
    day_rows = db.session.execute(
        select(day, func.count(ActivityEntry.id))
        .where(ActivityEntry.board_id == board_id)
        .group_by(day)
        .order_by(day)
    ).all()
    activity_by_day: list[dict[str, Any]] = [
        {"day": d.isoformat() if isinstance(d, date) else str(d), "count": int(n)}
        for d, n in day_rows
    ]

    return {
        "total_cards": sum(item["count"] for item in per_column),
        "per_column": per_column,
        "completion_rate": compute_completion_rate(
            (name, int(count)) for _, name, count in column_rows
        ),
        "activity_by_day": activity_by_day,
    }

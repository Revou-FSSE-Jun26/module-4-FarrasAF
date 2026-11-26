"""Property 17: Activity entries are recorded faithfully for each tracked event.

**Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 8.11, 8.13**
"""

from collections.abc import Callable
from typing import Any
from uuid import UUID

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import select

from flask_app.access.service import add_member_service, remove_member_service
from flask_app.activity.service import list_activity_service
from flask_app.cards.service import (
    create_card_service,
    delete_card_service,
    move_card_service,
    update_card_service,
)
from flask_app.columns.service import create_column_service, delete_column_service
from flask_app.comments.service import (
    create_comment_service,
    delete_comment_service,
    update_comment_service,
)
from flask_app.common.time import utc_now

from flask_app.models import ActivityEntry, TeamMembership, User  # isort: skip

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

_EVENTS = [
    "card_created",
    "card_updated",
    "card_moved",
    "card_deleted",
    "comment_created",
    "comment_edited",
    "comment_deleted",
    "column_created",
    "column_deleted",
    "member_joined",
    "member_removed",
]

_text = st.text(alphabet=st.characters(whitelist_categories=("L", "N")), min_size=1, max_size=40)


# Feature: task-management-app, Property 17: Activity entries are recorded faithfully for each tracked event  # noqa: E501
@_SETTINGS
@given(
    events=st.lists(st.sampled_from(_EVENTS), min_size=1, max_size=15),
    text=_text,
)
def test_activity_entries_recorded_faithfully(
    db_session: Any,
    make_user: Callable[..., User],
    make_board: Callable[..., Any],
    make_column: Callable[..., Any],
    make_card: Callable[..., Any],
    events: list[str],
    text: str,
) -> None:
    actor = make_user()
    other = make_user()
    board = make_board(admin=actor)
    db_session.add(
        TeamMembership(team_id=board.team_id, user_id=other.id, team_role="team_regular")
    )
    db_session.flush()
    source = make_column(board=board, name="Source")
    target = make_column(board=board, name="Target")
    card = make_card(column=source, created_by=actor)
    comment = create_comment_service(card.id, {"body": "seed"}, actor)
    # Seeding writes entries too; only entries after this point are compared.
    seeded = set(db_session.scalars(select(ActivityEntry.id)).all())
    is_member = False
    expected: list[tuple[str, UUID, UUID | None]] = []

    for event in events:
        before = utc_now()
        resource: UUID
        secondary: UUID | None = None
        if event == "card_created":
            resource = create_card_service(source.id, {"title": text}, actor)["id"]
        elif event == "card_updated":
            current = update_card_service(card.id, {"title": text, "version": card.version}, actor)
            db_session.refresh(card)
            assert current["version"] == card.version
            resource = card.id
        elif event == "card_moved":
            destination = target if card.column_id == source.id else source
            move_card_service(card.id, destination.id, 0, actor)
            db_session.refresh(card)
            resource = card.id
        elif event == "card_deleted":
            doomed = make_card(column=source, created_by=actor)
            resource = doomed.id
            delete_card_service(doomed.id, actor)
        elif event == "comment_created":
            resource = create_comment_service(card.id, {"body": text}, actor)["id"]
            secondary = card.id
        elif event == "comment_edited":
            updated = update_comment_service(
                comment["id"], {"body": text, "version": comment["version"]}, actor
            )
            comment = updated
            resource = comment["id"]
            secondary = card.id
        elif event == "comment_deleted":
            victim = create_comment_service(card.id, {"body": "tmp"}, actor)
            resource = victim["id"]
            secondary = card.id
            delete_comment_service(victim["id"], actor)
        elif event == "column_created":
            resource = create_column_service(board.id, {"name": text}, actor)["id"]
        elif event == "column_deleted":
            empty = make_column(board=board, name="Empty")
            resource = empty.id
            delete_column_service(empty.id, actor)
        elif event == "member_joined":
            if is_member:
                continue
            add_member_service(board.id, {"user_id": other.id, "role": "member"}, actor)
            is_member = True
            resource = other.id
        else:  # member_removed
            if not is_member:
                continue
            remove_member_service(board.id, other.id, actor)
            is_member = False
            resource = other.id
        after = utc_now()
        expected.append((event, resource, secondary))
        newest = db_session.scalars(
            select(ActivityEntry)
            .where(
                ActivityEntry.board_id == board.id,
                ActivityEntry.event_type == event,
                ActivityEntry.resource_id == resource,
                ActivityEntry.id.not_in(seeded),
            )
            .order_by(ActivityEntry.created_at.desc())
        ).first()
        assert newest is not None
        assert newest.actor_id == actor.id
        assert newest.secondary_resource_id == secondary
        assert newest.created_at is not None
        assert before <= newest.created_at <= after
        seeded.add(newest.id)

    # 8.13: listed entries carry event type, timestamp, actor and resource id.
    # Far fewer entries than one page (100), so page 0 holds all of them.
    page = list_activity_service(board.id, {"page": 0})["items"]
    listed = {(i["event_type"], i["resource_id"], i["secondary_resource_id"]) for i in page}
    for item in page:
        assert item["created_at"] is not None
        assert item["actor"]["id"] == actor.id
        assert item["resource_id"] is not None
    for entry in expected:
        assert entry in listed

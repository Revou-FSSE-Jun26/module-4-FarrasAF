"""attachment activity event types
Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-11-27 12:05:00.000000
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'f7a8b9c0d1e2'
down_revision = 'e6f7a8b9c0d1'
branch_labels = None
depends_on = None

OLD_EVENTS = ('card_created', 'card_updated', 'card_moved', 'card_deleted', 'comment_created', 'comment_edited', 'comment_deleted', 'column_created', 'column_deleted', 'member_joined', 'member_removed')
NEW_EVENTS = OLD_EVENTS + ('attachment_added', 'attachment_deleted')


def _condition(events):
    return "event_type IN (" + ", ".join(f"'{e}'" for e in events) + ")"


def upgrade():
    op.drop_constraint(op.f('ck_activity_entries_event_type'), 'activity_entries', type_='check')
    op.create_check_constraint(op.f('ck_activity_entries_event_type'), 'activity_entries', _condition(NEW_EVENTS))


def downgrade():
    # Entries of the new types cannot satisfy the old constraint, so remove them first.
    op.execute("DELETE FROM activity_entries WHERE event_type IN ('attachment_added', 'attachment_deleted')")
    op.drop_constraint(op.f('ck_activity_entries_event_type'), 'activity_entries', type_='check')
    op.create_check_constraint(op.f('ck_activity_entries_event_type'), 'activity_entries', _condition(OLD_EVENTS))

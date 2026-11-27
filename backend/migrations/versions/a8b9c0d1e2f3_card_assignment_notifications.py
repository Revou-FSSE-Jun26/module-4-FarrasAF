"""card assignment notifications
Revision ID: a8b9c0d1e2f3
Revises: f7a8b9c0d1e2
Create Date: 2026-11-27 15:00:00.000000
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'a8b9c0d1e2f3'
down_revision = 'f7a8b9c0d1e2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        # Existing rows are all comment mentions, so the default backfills them.
        batch_op.add_column(
            sa.Column('type', sa.String(length=50), nullable=False, server_default='comment_mention')
        )
        batch_op.add_column(sa.Column('card_id', sa.Uuid(), nullable=True))
        batch_op.alter_column('comment_id', existing_type=sa.Uuid(), nullable=True)
        batch_op.create_foreign_key(
            batch_op.f('fk_notifications_card_id_cards'), 'cards', ['card_id'], ['id'], ondelete='CASCADE'
        )
        batch_op.create_index(batch_op.f('ix_notifications_card_id'), ['card_id'], unique=False)
        batch_op.create_check_constraint(
            batch_op.f('ck_notifications_type'), "type IN ('comment_mention', 'card_assigned')"
        )
        batch_op.create_check_constraint(
            batch_op.f('ck_notifications_type_target'),
            "(type = 'comment_mention' AND comment_id IS NOT NULL)"
            " OR (type = 'card_assigned' AND card_id IS NOT NULL)",
        )
        batch_op.alter_column('type', existing_type=sa.String(length=50), server_default=None)


def downgrade():
    # Assignment Notifications have no Comment, so they cannot exist in the old shape.
    op.execute("DELETE FROM notifications WHERE type = 'card_assigned'")
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('ck_notifications_type_target'), type_='check')
        batch_op.drop_constraint(batch_op.f('ck_notifications_type'), type_='check')
        batch_op.drop_index(batch_op.f('ix_notifications_card_id'))
        batch_op.drop_constraint(batch_op.f('fk_notifications_card_id_cards'), type_='foreignkey')
        batch_op.alter_column('comment_id', existing_type=sa.Uuid(), nullable=False)
        batch_op.drop_column('card_id')
        batch_op.drop_column('type')

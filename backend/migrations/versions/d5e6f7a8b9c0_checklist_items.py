"""checklist items
Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-11-26 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd5e6f7a8b9c0'
down_revision = 'c4d5e6f7a8b9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('checklist_items',
    sa.Column('card_id', sa.Uuid(), nullable=False),
    sa.Column('text', sa.String(length=255), nullable=False),
    sa.Column('is_done', sa.Boolean(), nullable=False),
    sa.Column('order_index', sa.Integer(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['card_id'], ['cards.id'], name=op.f('fk_checklist_items_card_id_cards'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_checklist_items'))
    )
    with op.batch_alter_table('checklist_items', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_checklist_items_card_id'), ['card_id'], unique=False)


def downgrade():
    with op.batch_alter_table('checklist_items', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_checklist_items_card_id'))

    op.drop_table('checklist_items')

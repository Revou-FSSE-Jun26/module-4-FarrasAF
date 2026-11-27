"""attachments
Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-11-27 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e6f7a8b9c0d1'
down_revision = 'd5e6f7a8b9c0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('attachments',
    sa.Column('card_id', sa.Uuid(), nullable=False),
    sa.Column('uploaded_by_id', sa.Uuid(), nullable=False),
    sa.Column('file_name', sa.String(length=255), nullable=False),
    sa.Column('content_type', sa.String(length=255), nullable=False),
    sa.Column('size_bytes', sa.Integer(), nullable=False),
    sa.Column('url', sa.Text(), nullable=False),
    sa.Column('public_id', sa.String(length=255), nullable=False),
    sa.Column('resource_type', sa.String(length=50), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("resource_type IN ('image', 'raw')", name=op.f('ck_attachments_resource_type')),
    sa.ForeignKeyConstraint(['card_id'], ['cards.id'], name=op.f('fk_attachments_card_id_cards'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['uploaded_by_id'], ['users.id'], name=op.f('fk_attachments_uploaded_by_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_attachments'))
    )
    with op.batch_alter_table('attachments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_attachments_card_id'), ['card_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_attachments_uploaded_by_id'), ['uploaded_by_id'], unique=False)


def downgrade():
    with op.batch_alter_table('attachments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_attachments_uploaded_by_id'))
        batch_op.drop_index(batch_op.f('ix_attachments_card_id'))

    op.drop_table('attachments')

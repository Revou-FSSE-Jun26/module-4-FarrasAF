"""activity entry details
Revision ID: c4d5e6f7a8b9
Revises: 91b82f362644
Create Date: 2026-11-26 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c4d5e6f7a8b9'
down_revision = '91b82f362644'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('activity_entries', sa.Column('details', sa.JSON(), nullable=True))


def downgrade():
    op.drop_column('activity_entries', 'details')

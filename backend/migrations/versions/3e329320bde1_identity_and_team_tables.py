"""identity and team tables

Revision ID: 3e329320bde1
Revises: 
Create Date: 2026-11-14 11:41:17.258109

Migration (a): users, refresh_tokens, teams, team_memberships, team_join_links.
Board tables (b) and comment/notification/activity tables (c) are separate migrations.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3e329320bde1'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('teams',
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_teams'))
    )
    op.create_table('users',
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('display_name', sa.String(length=255), nullable=False),
    sa.Column('failed_login_attempts', sa.Integer(), nullable=False),
    sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
    sa.UniqueConstraint('email', name=op.f('uq_users_email'))
    )
    op.create_table('refresh_tokens',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('token_hash', sa.String(length=255), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_refresh_tokens_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_refresh_tokens')),
    sa.UniqueConstraint('token_hash', name=op.f('uq_refresh_tokens_token_hash'))
    )
    with op.batch_alter_table('refresh_tokens', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_refresh_tokens_user_id'), ['user_id'], unique=False)

    op.create_table('team_join_links',
    sa.Column('team_id', sa.Uuid(), nullable=False),
    sa.Column('token', sa.String(length=255), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_by_id', sa.Uuid(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("status IN ('active', 'inactive')", name=op.f('ck_team_join_links_status')),
    sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], name=op.f('fk_team_join_links_created_by_id_users')),
    sa.ForeignKeyConstraint(['team_id'], ['teams.id'], name=op.f('fk_team_join_links_team_id_teams'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_team_join_links')),
    sa.UniqueConstraint('token', name=op.f('uq_team_join_links_token'))
    )
    with op.batch_alter_table('team_join_links', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_team_join_links_created_by_id'), ['created_by_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_team_join_links_team_id'), ['team_id'], unique=False)

    op.create_table('team_memberships',
    sa.Column('team_id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('team_role', sa.String(length=50), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("team_role IN ('team_admin', 'team_regular')", name=op.f('ck_team_memberships_team_role')),
    sa.ForeignKeyConstraint(['team_id'], ['teams.id'], name=op.f('fk_team_memberships_team_id_teams'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_team_memberships_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_team_memberships')),
    sa.UniqueConstraint('team_id', 'user_id', name=op.f('uq_team_memberships_team_id'))
    )
    with op.batch_alter_table('team_memberships', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_team_memberships_team_id'), ['team_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_team_memberships_user_id'), ['user_id'], unique=False)


def downgrade():
    with op.batch_alter_table('team_memberships', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_team_memberships_user_id'))
        batch_op.drop_index(batch_op.f('ix_team_memberships_team_id'))

    op.drop_table('team_memberships')
    with op.batch_alter_table('team_join_links', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_team_join_links_team_id'))
        batch_op.drop_index(batch_op.f('ix_team_join_links_created_by_id'))

    op.drop_table('team_join_links')
    with op.batch_alter_table('refresh_tokens', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_refresh_tokens_user_id'))

    op.drop_table('refresh_tokens')
    op.drop_table('users')
    op.drop_table('teams')

"""board column card and access tables

Revision ID: b1a2c3d4e5f6
Revises: 3e329320bde1
Create Date: 2026-11-14 12:50:12.080383

Migration (b): boards, board_memberships, columns, cards, invitation_links.
Comment, notification, and activity tables are migration (c).
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b1a2c3d4e5f6"
down_revision = "3e329320bde1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "boards",
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("visibility", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('active', 'archived')", name=op.f("ck_boards_status")),
        sa.CheckConstraint("visibility IN ('private', 'team')", name=op.f("ck_boards_visibility")),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], name=op.f("fk_boards_team_id_teams")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_boards")),
    )
    with op.batch_alter_table("boards", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_boards_team_id"), ["team_id"], unique=False)

    op.create_table(
        "board_memberships",
        sa.Column("board_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("role IN ('member', 'admin')", name=op.f("ck_board_memberships_role")),
        sa.ForeignKeyConstraint(
            ["board_id"],
            ["boards.id"],
            name=op.f("fk_board_memberships_board_id_boards"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_board_memberships_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_board_memberships")),
        sa.UniqueConstraint("board_id", "user_id", name=op.f("uq_board_memberships_board_id")),
    )
    with op.batch_alter_table("board_memberships", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_board_memberships_board_id"), ["board_id"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_board_memberships_user_id"), ["user_id"], unique=False)

    op.create_table(
        "columns",
        sa.Column("board_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["board_id"], ["boards.id"], name=op.f("fk_columns_board_id_boards"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_columns")),
        sa.UniqueConstraint(
            "board_id",
            "order_index",
            deferrable=True,
            initially="DEFERRED",
            name=op.f("uq_columns_board_id"),
        ),
    )
    with op.batch_alter_table("columns", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_columns_board_id"), ["board_id"], unique=False)

    op.create_table(
        "invitation_links",
        sa.Column("board_id", sa.Uuid(), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('active', 'inactive')", name=op.f("ck_invitation_links_status")
        ),
        sa.ForeignKeyConstraint(
            ["board_id"],
            ["boards.id"],
            name=op.f("fk_invitation_links_board_id_boards"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"], ["users.id"], name=op.f("fk_invitation_links_created_by_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_invitation_links")),
        sa.UniqueConstraint("token", name=op.f("uq_invitation_links_token")),
    )
    with op.batch_alter_table("invitation_links", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_invitation_links_board_id"), ["board_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_invitation_links_created_by_id"), ["created_by_id"], unique=False
        )

    # cards.updated_at has no server-side default or trigger: Card_Service sets it explicitly.
    # The deferred unique constraint (column_id, order_index) also serves as the
    # (column_id, order_index) lookup index.
    op.create_table(
        "cards",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("column_id", sa.Uuid(), nullable=False),
        sa.Column("board_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("assignee_id", sa.Uuid(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["assignee_id"], ["users.id"], name=op.f("fk_cards_assignee_id_users")
        ),
        sa.ForeignKeyConstraint(
            ["board_id"], ["boards.id"], name=op.f("fk_cards_board_id_boards"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["column_id"],
            ["columns.id"],
            name=op.f("fk_cards_column_id_columns"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"], ["users.id"], name=op.f("fk_cards_created_by_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cards")),
        sa.UniqueConstraint(
            "column_id",
            "order_index",
            deferrable=True,
            initially="DEFERRED",
            name=op.f("uq_cards_column_id"),
        ),
    )
    with op.batch_alter_table("cards", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_cards_assignee_id"), ["assignee_id"], unique=False)
        batch_op.create_index(
            "ix_cards_board_id_lower_title",
            ["board_id", sa.literal_column("lower(title)")],
            unique=False,
        )
        batch_op.create_index(
            "ix_cards_board_id_updated_at_id",
            ["board_id", sa.literal_column("updated_at DESC"), sa.literal_column("id DESC")],
            unique=False,
        )
        batch_op.create_index(batch_op.f("ix_cards_created_by_id"), ["created_by_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("cards", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_cards_created_by_id"))
        batch_op.drop_index("ix_cards_board_id_updated_at_id")
        batch_op.drop_index("ix_cards_board_id_lower_title")
        batch_op.drop_index(batch_op.f("ix_cards_assignee_id"))

    op.drop_table("cards")
    with op.batch_alter_table("invitation_links", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_invitation_links_created_by_id"))
        batch_op.drop_index(batch_op.f("ix_invitation_links_board_id"))

    op.drop_table("invitation_links")
    with op.batch_alter_table("columns", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_columns_board_id"))

    op.drop_table("columns")
    with op.batch_alter_table("board_memberships", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_board_memberships_user_id"))
        batch_op.drop_index(batch_op.f("ix_board_memberships_board_id"))

    op.drop_table("board_memberships")
    with op.batch_alter_table("boards", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_boards_team_id"))

    op.drop_table("boards")

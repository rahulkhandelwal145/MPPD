"""Add is_loa column to mp_profiles

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002_add_missing_columns"
branch_labels = None
depend_on = None


def upgrade() -> None:
    op.add_column(
        "mp_profiles",
        sa.Column("is_loa", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_column("mp_profiles", "is_loa")

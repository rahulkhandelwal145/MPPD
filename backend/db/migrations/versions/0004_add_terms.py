"""Add terms column to mp_profiles

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depend_on = None


def upgrade() -> None:
    op.add_column(
        "mp_profiles",
        sa.Column("terms", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("mp_profiles", "terms")

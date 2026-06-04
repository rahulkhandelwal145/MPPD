"""Add image_url column to mp_profiles

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depend_on = None


def upgrade() -> None:
    op.add_column(
        "mp_profiles",
        sa.Column("image_url", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("mp_profiles", "image_url")

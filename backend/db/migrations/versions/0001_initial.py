"""Initial schema

Revision ID: 0001_initial
Revises: None
Create Date: 2026-05-31 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depend_on = None


def upgrade() -> None:
    op.create_table(
        "mp_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("prs_slug", sa.String(length=200), nullable=False, unique=True),
        sa.Column("constituency", sa.String(length=200), nullable=True),
        sa.Column("state", sa.String(length=100), nullable=True),
        sa.Column("party", sa.String(length=100), nullable=True),
        sa.Column("is_minister", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_speaker", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("lok_sabha_term", sa.Integer(), nullable=False, server_default=sa.text("18")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_table(
        "mp_raw_data",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("mp_id", sa.Integer(), sa.ForeignKey("mp_profiles.id"), nullable=False),
        sa.Column("attendance_pct", sa.Float(), nullable=True),
        sa.Column("questions_count", sa.Integer(), nullable=True),
        sa.Column("debates_count", sa.Integer(), nullable=True),
        sa.Column("pmb_count", sa.Integer(), nullable=True),
        sa.Column("mplads_utilization", sa.Float(), nullable=True),
        sa.Column("scraped_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_table(
        "mp_scores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("mp_id", sa.Integer(), sa.ForeignKey("mp_profiles.id"), nullable=False),
        sa.Column("peer_group", sa.String(length=20), nullable=False),
        sa.Column("attendance_score", sa.Float(), nullable=True),
        sa.Column("questions_score", sa.Float(), nullable=True),
        sa.Column("debates_score", sa.Float(), nullable=True),
        sa.Column("pmb_score", sa.Float(), nullable=True),
        sa.Column("attendance_rank", sa.Integer(), nullable=True),
        sa.Column("questions_rank", sa.Integer(), nullable=True),
        sa.Column("debates_rank", sa.Integer(), nullable=True),
        sa.Column("pmb_rank", sa.Integer(), nullable=True),
        sa.Column("total_peers", sa.Integer(), nullable=False),
        sa.Column("scored_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_table(
        "pipeline_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("mps_scraped", sa.Integer(), nullable=True),
        sa.Column("mps_scored", sa.Integer(), nullable=True),
        sa.Column("errors", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("pipeline_runs")
    op.drop_table("mp_scores")
    op.drop_table("mp_raw_data")
    op.drop_table("mp_profiles")

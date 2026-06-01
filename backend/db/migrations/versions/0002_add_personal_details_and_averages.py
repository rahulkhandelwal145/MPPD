"""Add personal details and national averages

Revision ID: 0002
Revises: 0001_initial
Create Date: 2026-06-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0002"
down_revision = "0001_initial"
branch_labels = None
depend_on = None


def upgrade() -> None:
    # Add personal details columns to mp_profiles
    op.add_column('mp_profiles', sa.Column('age', sa.Integer(), nullable=True))
    op.add_column('mp_profiles', sa.Column('gender', sa.String(length=50), nullable=True))
    op.add_column('mp_profiles', sa.Column('education', sa.String(length=500), nullable=True))
    
    # Add national and state average columns to mp_raw_data
    op.add_column('mp_raw_data', sa.Column('national_avg_attendance', sa.Float(), nullable=True))
    op.add_column('mp_raw_data', sa.Column('state_avg_attendance', sa.Float(), nullable=True))
    op.add_column('mp_raw_data', sa.Column('national_avg_questions', sa.Float(), nullable=True))
    op.add_column('mp_raw_data', sa.Column('state_avg_questions', sa.Float(), nullable=True))
    op.add_column('mp_raw_data', sa.Column('national_avg_debates', sa.Float(), nullable=True))
    op.add_column('mp_raw_data', sa.Column('state_avg_debates', sa.Float(), nullable=True))
    op.add_column('mp_raw_data', sa.Column('national_avg_pmb', sa.Float(), nullable=True))
    op.add_column('mp_raw_data', sa.Column('state_avg_pmb', sa.Float(), nullable=True))


def downgrade() -> None:
    # Remove columns from mp_raw_data
    op.drop_column('mp_raw_data', 'state_avg_pmb')
    op.drop_column('mp_raw_data', 'national_avg_pmb')
    op.drop_column('mp_raw_data', 'state_avg_debates')
    op.drop_column('mp_raw_data', 'national_avg_debates')
    op.drop_column('mp_raw_data', 'state_avg_questions')
    op.drop_column('mp_raw_data', 'national_avg_questions')
    op.drop_column('mp_raw_data', 'state_avg_attendance')
    op.drop_column('mp_raw_data', 'national_avg_attendance')
    
    # Remove columns from mp_profiles
    op.drop_column('mp_profiles', 'education')
    op.drop_column('mp_profiles', 'gender')
    op.drop_column('mp_profiles', 'age')

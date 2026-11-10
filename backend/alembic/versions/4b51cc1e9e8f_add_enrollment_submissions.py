"""add_enrollment_submissions

Revision ID: 4b51cc1e9e8f
Revises: 3a42e90c6daf
Create Date: 2026-11-09 22:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b51cc1e9e8f'
down_revision: Union[str, None] = '3a42e90c6daf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'enrollment_submissions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('roll_number', sa.String(length=50), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('institutional_email', sa.String(length=255), nullable=False),
        sa.Column('department', sa.String(length=100), nullable=False),
        sa.Column('academic_year', sa.String(length=50), nullable=False),
        sa.Column('cohort_id', sa.String(length=36), nullable=True),
        sa.Column('photo_storage_path', sa.String(length=500), nullable=False),
        sa.Column('photo_sha256', sa.String(length=64), nullable=False),
        sa.Column('photo_mime', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('consent_acknowledged', sa.Boolean(), nullable=False),
        sa.Column('rejection_reason', sa.String(length=500), nullable=True),
        sa.Column('reviewed_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['cohort_id'], ['cohorts.id']),
        sa.ForeignKeyConstraint(['reviewed_by_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_submission_roll', 'enrollment_submissions', ['roll_number'])
    op.create_index('idx_submission_status_created', 'enrollment_submissions', ['status', 'created_at'])


def downgrade() -> None:
    op.drop_index('idx_submission_status_created', table_name='enrollment_submissions')
    op.drop_index('idx_submission_roll', table_name='enrollment_submissions')
    op.drop_table('enrollment_submissions')

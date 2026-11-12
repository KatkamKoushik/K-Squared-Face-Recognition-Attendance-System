"""add student lifecycle and data corrections

Revision ID: 6d73ee3e8b8b
Revises: 5c62dd2f0b7a
Create Date: 2026-11-12 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6d73ee3e8b8b'
down_revision: Union[str, None] = '5c62dd2f0b7a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add lifecycle_status to students table
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    student_cols = [c["name"] for c in inspector.get_columns("students")]

    if "lifecycle_status" not in student_cols:
        op.add_column(
            "students",
            sa.Column("lifecycle_status", sa.String(length=20), nullable=False, server_default="ACTIVE"),
        )

    # 2. Create student_data_corrections table if not exists
    tables = inspector.get_table_names()
    if "student_data_corrections" not in tables:
        op.create_table(
            "student_data_corrections",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("student_id", sa.String(length=36), sa.ForeignKey("students.id"), nullable=False),
            sa.Column("field_name", sa.String(length=50), nullable=False),
            sa.Column("requested_value", sa.String(length=255), nullable=False),
            sa.Column("current_value", sa.String(length=255), nullable=True),
            sa.Column("reason", sa.String(length=500), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
            sa.Column("review_notes", sa.String(length=500), nullable=True),
            sa.Column("reviewed_by_user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index(
            "idx_correction_student_status",
            "student_data_corrections",
            ["student_id", "status"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_index("idx_correction_student_status", table_name="student_data_corrections")
    op.drop_table("student_data_corrections")
    op.drop_column("students", "lifecycle_status")

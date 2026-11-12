"""enable rls and add fk indexes

Revision ID: 7e84ff4f9c9c
Revises: 6d73ee3e8b8b
Create Date: 2026-11-12 23:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7e84ff4f9c9c'
down_revision: Union[str, None] = '6d73ee3e8b8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add missing foreign key indexes on student_data_corrections
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = [idx["name"] for idx in inspector.get_indexes("student_data_corrections")]

    if "idx_fk_student_data_corrections_student" not in indexes:
        op.create_index(
            "idx_fk_student_data_corrections_student",
            "student_data_corrections",
            ["student_id"],
            unique=False,
        )

    if "idx_fk_student_data_corrections_reviewed_by" not in indexes:
        op.create_index(
            "idx_fk_student_data_corrections_reviewed_by",
            "student_data_corrections",
            ["reviewed_by_user_id"],
            unique=False,
        )

    # 2. Enable RLS on alembic_version and student_data_corrections (PostgreSQL only)
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE public.alembic_version ENABLE ROW LEVEL SECURITY;")
        op.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_policies WHERE tablename = 'alembic_version' AND policyname = 'service_role_all'
                ) THEN
                    CREATE POLICY service_role_all ON public.alembic_version FOR ALL TO service_role USING (true) WITH CHECK (true);
                END IF;
            END $$;
        """)

        op.execute("ALTER TABLE public.student_data_corrections ENABLE ROW LEVEL SECURITY;")
        op.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_policies WHERE tablename = 'student_data_corrections' AND policyname = 'service_role_all'
                ) THEN
                    CREATE POLICY service_role_all ON public.student_data_corrections FOR ALL TO service_role USING (true) WITH CHECK (true);
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM pg_policies WHERE tablename = 'student_data_corrections' AND policyname = 'authenticated_select'
                ) THEN
                    CREATE POLICY authenticated_select ON public.student_data_corrections FOR SELECT TO authenticated USING (true);
                END IF;
            END $$;
        """)


    # 3. Drop redundant single-column duplicate indexes subsumed by composite indexes
    submission_indexes = [idx["name"] for idx in inspector.get_indexes("enrollment_submissions")]
    if "ix_enrollment_submissions_status" in submission_indexes:
        op.drop_index("ix_enrollment_submissions_status", table_name="enrollment_submissions")

    job_indexes = [idx["name"] for idx in inspector.get_indexes("vision_jobs")]
    if "ix_vision_jobs_status" in job_indexes:
        op.drop_index("ix_vision_jobs_status", table_name="vision_jobs")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    job_indexes = [idx["name"] for idx in inspector.get_indexes("vision_jobs")]
    if "ix_vision_jobs_status" not in job_indexes:
        op.create_index("ix_vision_jobs_status", "vision_jobs", ["status"])

    submission_indexes = [idx["name"] for idx in inspector.get_indexes("enrollment_submissions")]
    if "ix_enrollment_submissions_status" not in submission_indexes:
        op.create_index("ix_enrollment_submissions_status", "enrollment_submissions", ["status"])

    if bind.dialect.name == "postgresql":
        op.execute("DROP POLICY IF EXISTS authenticated_select ON public.student_data_corrections;")
        op.execute("DROP POLICY IF EXISTS service_role_all ON public.student_data_corrections;")
        op.execute("ALTER TABLE public.student_data_corrections DISABLE ROW LEVEL SECURITY;")
        op.execute("DROP POLICY IF EXISTS service_role_all ON public.alembic_version;")
        op.execute("ALTER TABLE public.alembic_version DISABLE ROW LEVEL SECURITY;")

    op.drop_index("idx_fk_student_data_corrections_reviewed_by", table_name="student_data_corrections")
    op.drop_index("idx_fk_student_data_corrections_student", table_name="student_data_corrections")

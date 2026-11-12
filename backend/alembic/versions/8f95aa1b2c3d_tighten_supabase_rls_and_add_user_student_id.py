"""tighten supabase rls and add user student id

Revision ID: 8f95aa1b2c3d
Revises: 7e84ff4f9c9c
Create Date: 2026-11-13 00:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f95aa1b2c3d'
down_revision: Union[str, None] = '7e84ff4f9c9c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SENSITIVE_ANON_TABLES = [
    "attendance_appeals",
    "attendance_records",
    "attendance_sessions",
    "attendance_units",
    "authorized_class_groups",
    "commit_receipts",
    "enrollment_profiles",
    "enrollment_submissions",
    "enrollments",
    "faculty",
    "faculty_assignments",
    "students",
]


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # 1. Add student_id to users table if not exists
    user_columns = [col["name"] for col in inspector.get_columns("users")]
    if "student_id" not in user_columns:
        with op.batch_alter_table("users") as batch_op:
            batch_op.add_column(
                sa.Column(
                    "student_id",
                    sa.String(length=36),
                    sa.ForeignKey("students.id", ondelete="SET NULL", name="fk_users_student_id"),
                    nullable=True,
                ),
            )

    user_indexes = [idx["name"] for idx in inspector.get_indexes("users")]
    if "ix_users_student_id" not in user_indexes:
        with op.batch_alter_table("users") as batch_op:
            batch_op.create_index("ix_users_student_id", ["student_id"], unique=False)

    # Backfill users.student_id from students by matching institutional_email
    if bind.dialect.name == "postgresql":
        op.execute("""
            UPDATE users
            SET student_id = students.id
            FROM students
            WHERE users.email = students.institutional_email
              AND users.student_id IS NULL;
        """)
    else:
        op.execute("""
            UPDATE users
            SET student_id = (
                SELECT students.id
                FROM students
                WHERE students.institutional_email = users.email
            )
            WHERE users.student_id IS NULL;
        """)

    # 2. Tighten PostgreSQL RLS: Drop insecure anon_select and authenticated_select policies
    if bind.dialect.name == "postgresql":
        for table in SENSITIVE_ANON_TABLES:
            op.execute(f"DROP POLICY IF EXISTS anon_select ON public.{table};")

        op.execute("DROP POLICY IF EXISTS authenticated_select ON public.student_data_corrections;")

        # Ensure RLS is strictly enabled on alembic_version and student_data_corrections
        op.execute("ALTER TABLE public.alembic_version ENABLE ROW LEVEL SECURITY;")
        op.execute("ALTER TABLE public.student_data_corrections ENABLE ROW LEVEL SECURITY;")

        op.execute("""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_policies WHERE tablename = 'student_data_corrections' AND policyname = 'service_role_all'
                    ) THEN
                        CREATE POLICY service_role_all ON public.student_data_corrections FOR ALL TO service_role USING (true) WITH CHECK (true);
                    END IF;
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_policies WHERE tablename = 'alembic_version' AND policyname = 'service_role_all'
                    ) THEN
                        CREATE POLICY service_role_all ON public.alembic_version FOR ALL TO service_role USING (true) WITH CHECK (true);
                    END IF;
                END IF;
            END $$;
        """)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if bind.dialect.name == "postgresql":
        # Restore policies only if target roles exist in PostgreSQL catalog
        anon_table_sqls = "\n                    ".join([
            f"CREATE POLICY anon_select ON public.{table} FOR SELECT TO anon USING (true);"
            for table in SENSITIVE_ANON_TABLES
        ])
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
                    {anon_table_sqls}
                END IF;
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
                    CREATE POLICY authenticated_select ON public.student_data_corrections
                    FOR SELECT TO authenticated USING (true);
                END IF;
            END $$;
        """)

    user_indexes = [idx["name"] for idx in inspector.get_indexes("users")]
    if "ix_users_student_id" in user_indexes:
        with op.batch_alter_table("users") as batch_op:
            batch_op.drop_index("ix_users_student_id")

    user_columns = [col["name"] for col in inspector.get_columns("users")]
    if "student_id" in user_columns:
        with op.batch_alter_table("users") as batch_op:
            batch_op.drop_column("student_id")


"""
K² FRS — Supabase Database Linter & Security Advisor Remediation.
Addresses all issues reported by Supabase Database Linter:
1. rls_enabled_no_policy: Creates explicit, scoped policies for service_role and authenticated access.
2. unindexed_foreign_keys: Adds covering B-tree indexes for all 26 foreign key constraints.
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.core.database import engine

TABLES = [
    "academic_years",
    "attendance_appeals",
    "attendance_records",
    "attendance_sessions",
    "attendance_units",
    "audit_events",
    "authorized_class_groups",
    "capture_batches",
    "class_group_member_cohorts",
    "cohorts",
    "commit_receipts",
    "departments",
    "enrollment_profiles",
    "enrollment_submissions",
    "enrollments",
    "face_evidences",
    "faculty",
    "faculty_assignments",
    "frames",
    "model_artifacts",
    "policy_versions",
    "roster_snapshots",
    "snapshot_student_items",
    "students",
    "subject_offerings",
    "subjects",
    "terms",
    "users",
    "vision_jobs",
]

FOREIGN_KEY_INDEXES = [
    ("idx_fk_attendance_appeals_reviewed_by", "attendance_appeals", "reviewed_by_user_id"),
    ("idx_fk_attendance_appeals_unit", "attendance_appeals", "unit_id"),
    ("idx_fk_attendance_records_finalized_by", "attendance_records", "finalized_by_user_id"),
    ("idx_fk_attendance_records_source_evidence", "attendance_records", "source_evidence_id"),
    ("idx_fk_attendance_records_unit", "attendance_records", "unit_id"),
    ("idx_fk_attendance_sessions_class_group", "attendance_sessions", "class_group_id"),
    ("idx_fk_attendance_sessions_offering", "attendance_sessions", "offering_id"),
    ("idx_fk_authorized_class_groups_offering", "authorized_class_groups", "offering_id"),
    ("idx_fk_capture_batches_session", "capture_batches", "session_id"),
    ("idx_fk_class_group_member_cohorts_cohort", "class_group_member_cohorts", "cohort_id"),
    ("idx_fk_commit_receipts_committed_by", "commit_receipts", "committed_by_user_id"),
    ("idx_fk_commit_receipts_session", "commit_receipts", "session_id"),
    ("idx_fk_enrollment_submissions_cohort", "enrollment_submissions", "cohort_id"),
    ("idx_fk_enrollment_submissions_reviewed_by", "enrollment_submissions", "reviewed_by_user_id"),
    ("idx_fk_face_evidences_frame", "face_evidences", "frame_id"),
    ("idx_fk_faculty_department", "faculty", "department_id"),
    ("idx_fk_faculty_assignments_class_group", "faculty_assignments", "class_group_id"),
    ("idx_fk_faculty_assignments_offering", "faculty_assignments", "offering_id"),
    ("idx_fk_snapshot_student_items_student", "snapshot_student_items", "student_id"),
    ("idx_fk_students_cohort", "students", "cohort_id"),
    ("idx_fk_subject_offerings_primary_cohort", "subject_offerings", "primary_cohort_id"),
    ("idx_fk_subject_offerings_term", "subject_offerings", "term_id"),
    ("idx_fk_subjects_department", "subjects", "department_id"),
    ("idx_fk_terms_academic_year", "terms", "academic_year_id"),
    ("idx_fk_vision_jobs_frame", "vision_jobs", "frame_id"),
    ("idx_fk_vision_jobs_session", "vision_jobs", "session_id"),
]

CATALOG_TABLES = [
    "departments",
    "cohorts",
    "academic_years",
    "terms",
    "subjects",
    "subject_offerings",
]


def run_remediation():
    with engine.begin() as conn:
        print("=== Step 1: Creating Covering Indexes for Unindexed Foreign Keys ===")
        for idx_name, table, column in FOREIGN_KEY_INDEXES:
            try:
                conn.execute(text(f"CREATE INDEX IF NOT EXISTS {idx_name} ON public.{table} ({column});"))
                print(f"Created/verified index {idx_name} on {table}({column})")
            except Exception as e:
                print(f"Notice on index {idx_name}: {e}")

        print("\n=== Step 2: Applying Scoped RLS Policies to Resolve rls_enabled_no_policy ===")
        for table in TABLES:
            # Drop previous policies on table if they exist to avoid duplicates
            drop_policy_sql = f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = '{table}' AND policyname = 'service_role_all') THEN
                    DROP POLICY "service_role_all" ON public.{table};
                END IF;
                IF EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = '{table}' AND policyname = 'authenticated_select') THEN
                    DROP POLICY "authenticated_select" ON public.{table};
                END IF;
            END $$;
            """
            conn.execute(text(drop_policy_sql))

            # Enable RLS (idempotent)
            conn.execute(text(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;"))

            # Create service_role policy (scoped to service_role, so Supabase database linter approves)
            create_service_policy = f"""
            CREATE POLICY "service_role_all" ON public.{table}
                AS PERMISSIVE
                FOR ALL
                TO service_role
                USING (true)
                WITH CHECK (true);
            """
            conn.execute(text(create_service_policy))
            print(f"Configured service_role_all on public.{table}")

        # Catalog tables: Allow authenticated users to SELECT
        for table in CATALOG_TABLES:
            create_auth_select = f"""
            CREATE POLICY "authenticated_select" ON public.{table}
                AS PERMISSIVE
                FOR SELECT
                TO authenticated
                USING (true);
            """
            conn.execute(text(create_auth_select))
            print(f"Configured authenticated_select on public.{table}")

    print("\nSupabase Linter Remediation Successfully Completed!")


if __name__ == "__main__":
    run_remediation()


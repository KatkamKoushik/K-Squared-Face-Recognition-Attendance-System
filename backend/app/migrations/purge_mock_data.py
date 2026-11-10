"""
FRS V7.1 K² — Purge Mock and Seed Data Script.
Removes:
- 22 seeded dummy students (roll numbers 00622501..00622522) and their profiles/enrollments.
- All dummy attendance sessions, units, records, receipts, and vision jobs.
- Automated E2E test submissions (roll numbers starting with 'E2E-').
Preserves:
- Authentic student submissions:
    - 24567T0929 (GUGULOTHU SANDEEP)
    - 24567T3019 (katkam koushik)
- Authentic academic hierarchy:
    - Departments (CSE, ECE, EEE, MECH, CIVIL, IT, CSD)
    - Cohorts, Academic Years, Terms, Subjects, Subject Offerings, Faculty
"""

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.core.database import engine

def purge_mock_and_seed_data():
    with engine.begin() as conn:
        print("Starting mock and seed data purge...")

        # 1. Clean attendance sessions and dependents
        print("Cleaning attendance sessions, records, appeals, and receipts...")
        conn.execute(text("DELETE FROM attendance_appeals;"))
        conn.execute(text("DELETE FROM attendance_records;"))
        conn.execute(text("DELETE FROM commit_receipts;"))
        conn.execute(text("DELETE FROM face_evidences;"))
        conn.execute(text("DELETE FROM vision_jobs;"))
        conn.execute(text("DELETE FROM frames;"))
        conn.execute(text("DELETE FROM capture_batches;"))
        conn.execute(text("DELETE FROM snapshot_student_items;"))
        conn.execute(text("DELETE FROM roster_snapshots;"))
        conn.execute(text("DELETE FROM attendance_units;"))
        conn.execute(text("DELETE FROM attendance_sessions;"))

        # 2. Clean dummy student enrollments and profiles
        print("Cleaning dummy student biometric profiles and enrollments...")
        conn.execute(text("""
            DELETE FROM enrollment_profiles 
            WHERE student_id IN (SELECT id FROM students WHERE roll_number LIKE '006225%' OR roll_number LIKE 'E2E-%');
        """))
        conn.execute(text("""
            DELETE FROM enrollments 
            WHERE student_id IN (SELECT id FROM students WHERE roll_number LIKE '006225%' OR roll_number LIKE 'E2E-%');
        """))

        # 3. Delete seeded dummy students and E2E students
        print("Deleting seeded dummy and E2E students...")
        res = conn.execute(text("DELETE FROM students WHERE roll_number LIKE '006225%' OR roll_number LIKE 'E2E-%';"))
        print(f"Deleted {res.rowcount} students.")

        # 4. Clean automated E2E test enrollment submissions
        print("Cleaning automated test enrollment submissions (E2E-%)...")
        res_subs = conn.execute(text("DELETE FROM enrollment_submissions WHERE roll_number LIKE 'E2E-%';"))
        print(f"Deleted {res_subs.rowcount} automated test submissions.")

        # 5. Audit retained real submissions
        retained = conn.execute(text("""
            SELECT id, roll_number, full_name, status, department, created_at 
            FROM enrollment_submissions 
            ORDER BY created_at ASC;
        """)).fetchall()

        print("\n=== Retained Authentic Student Submissions ===")
        for s in retained:
            print(f"- Roll: {s.roll_number} | Name: {s.full_name} | Dept: {s.department} | Status: {s.status}")

        # 6. Audit total students count
        total_students = conn.execute(text("SELECT count(*) FROM students;")).scalar()
        print(f"\nRemaining Enrolled Students in database: {total_students}")

        total_sessions = conn.execute(text("SELECT count(*) FROM attendance_sessions;")).scalar()
        print(f"Remaining Attendance Sessions in database: {total_sessions}")

        print("\nPurge completed successfully!")

if __name__ == "__main__":
    purge_mock_and_seed_data()

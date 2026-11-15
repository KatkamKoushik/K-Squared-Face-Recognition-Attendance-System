"""
K² FRS — Delete All First Year Students.
Only deletes First Year (2026-2030 / 26567T...) students from PostgreSQL.
All other students (24567T3019 katkam koushik, 24567T0929, etc.) are strictly preserved.
"""

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.domain.models.student import Student, EnrollmentSubmission
from app.domain.models.academic import User
from app.services.academic_service import AcademicService
from sqlalchemy import text

def delete_all_first_years():
    db = SessionLocal()
    dev = db.query(User).filter(User.email == "koushikkatkam@gmail.com").first()
    if not dev:
        raise RuntimeError("Developer koushikkatkam@gmail.com not found")

    # Find First Year submissions
    first_year_subs = db.query(EnrollmentSubmission).filter(
        (EnrollmentSubmission.academic_year == "2026-2030 (First Year)") |
        (EnrollmentSubmission.roll_number.like("26567T%"))
    ).all()

    first_year_rolls = set(sub.roll_number for sub in first_year_subs)

    # Find First Year students
    first_year_students = db.query(Student).filter(
        (Student.roll_number.in_(first_year_rolls)) |
        (Student.roll_number.like("26567T%"))
    ).all()

    print(f"Found {len(first_year_students)} First Year students to delete:")
    for s in first_year_students:
        print(f"  Deleting: {s.roll_number} - {s.full_name}")

    deleted_count = 0
    for s in first_year_students:
        res = AcademicService.delete_student(
            db=db,
            student_id=s.id,
            user=dev,
            correlation_id=f"purge-first-year-{s.roll_number}",
        )
        deleted_count += 1

    # Clean up any remaining First Year submissions
    db.execute(text("""
        DELETE FROM enrollment_submissions 
        WHERE academic_year = '2026-2030 (First Year)' 
           OR roll_number LIKE '26567T%'
    """))
    db.commit()

    print(f"\nSuccessfully deleted {deleted_count} First Year students and purged all submissions.")

    # Show remaining students
    remaining = db.query(Student).all()
    print(f"\nRemaining students in database ({len(remaining)} total):")
    for r in remaining:
        print(f"  Preserved: {r.roll_number} - {r.full_name}")

if __name__ == "__main__":
    delete_all_first_years()

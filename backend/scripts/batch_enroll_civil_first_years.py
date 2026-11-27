"""
K² FRS — Batch Enrollment Script for Civil Engineering First-Year Students.
Enrolls 39 students into B.Tech CIVIL Class of 2030 (First Year I/IV):
- Validates image and face detection
- Uploads photo directly to Cloudinary
- Computes ArcFace 512-D, SFace 128-D, and Fine-Tuned 128-D embeddings
- Links to Cohort and generates unique institutional email
"""

import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.domain.models.academic import Cohort, Department
from app.domain.models.student import Student, EnrollmentProfile
from app.services.enrollment_service import EnrollmentService

# Student definition mapping: (suffix, name, filename, gender_group)
STUDENTS_DATA = [
    # Girls (24)
    (51, "Sreeja", "51.jpeg"),
    (62, "Spandana", "62.jpeg"),
    (28, "Sindhuja", "28.jpeg"),
    (55, "Sai Shivani", "55.jpeg"),
    (11, "Kalyani", "11.jpeg"),
    (15, "Bhagyasri", "15.jpeg"),
    (57, "Geethika", "57.jpeg"),
    (34, "Ramya", "34.jpeg"),
    (18, "Abhihasa", "18.jpeg"),
    (60, "Srilekha", "60.jpeg"),
    (46, "Greeshmika", "46.jpeg"),
    (36, "Anjali Devi", "36.jpeg"),
    (30, "Bindu", "30.jpeg"),
    (44, "Sandya", "44.jpeg"),
    (20, "Sirivally", "20.jpeg"),
    (2, "Varshini", "2.jpeg"),
    (54, "Niharika", "54.jpg"),
    (3, "Kavya Sri", "3.jpeg"),
    (59, "Gouthami", "59.jpeg"),
    (58, "Susmitha", "58.jpeg"),
    (48, "Rudrani", "48.jpg"),
    (39, "Reethu", "39.jpeg"),
    (10, "Indira", "10.jpeg"),
    # Soundharyao: image file is 9.jpeg, roll can be 07 or 09
    (7, "Soundharyao", "9.jpeg"),

    # Boys (15)
    (1, "Akhil", "01.jpeg"),
    (19, "Manoj", "19.jpeg"),
    (38, "Rahub", "38.jpeg"),
    (50, "Bharath Kumar", "50.jpeg"),
    (32, "Pranith", "32.jpeg"),
    (45, "Adithya", "45.jpeg"),
    (47, "Tarun Teja", "47.jpeg"),
    (49, "Bhanu Prasad", "49.jpeg"),
    (25, "Srikar", "25.jpeg"),
    (26, "Snehith", "26.jpeg"),
    (56, "Santhosh", "56.jpeg"),
    (23, "Sri Chaitanya Kanshiram", "23.jpeg"),
    (61, "Shivaji", "61.jpeg"),
    (27, "Sheshadri", "27.jpeg"),
    (31, "Bhanu Prasad", "31.jpeg"),
]


def format_roll(num: int) -> str:
    return f"26567T00{num:02d}"


def generate_email(name: str, num: int) -> str:
    clean = "".join(c for c in name.lower() if c.isalnum())
    return f"{clean}.{num:02d}@kucet.ac.in"


def run_batch_enrollment(soundharya_roll: int = 7):
    db = SessionLocal()
    try:
        civil_dept = db.query(Department).filter(Department.code == "CIVIL").first()
        if not civil_dept:
            print("ERROR: CIVIL department not found!")
            return

        cohort = db.query(Cohort).filter(
            Cohort.department_id == civil_dept.id,
            Cohort.admission_year == 2026,
            Cohort.graduation_year == 2030,
        ).first()

        if not cohort:
            print("ERROR: Cohort B.Tech CIVIL Class of 2030 not found!")
            return

        print(f"Target Cohort: {cohort.id} | {cohort.name}")
        students_dir = Path(__file__).resolve().parent.parent.parent / "students"

        total = len(STUDENTS_DATA)
        success_count = 0
        skipped_count = 0
        failed_count = 0

        for i, (num, name, filename) in enumerate(STUDENTS_DATA):
            actual_num = soundharya_roll if name == "Soundharyao" else num
            roll = format_roll(actual_num)
            email = generate_email(name, actual_num)
            filepath = students_dir / filename

            # Check if student already exists and enrolled
            existing = db.query(Student).filter(Student.roll_number == roll).first()
            if existing:
                profiles_count = db.query(EnrollmentProfile).filter(EnrollmentProfile.student_id == existing.id).count()
                if profiles_count >= 3:
                    print(f"[{i+1}/{total}] SKIP: {roll} ({name}) already enrolled with {profiles_count} profiles.")
                    skipped_count += 1
                    continue

            if not filepath.exists():
                print(f"[{i+1}/{total}] FAIL: File {filepath} does not exist for {name} ({roll})")
                failed_count += 1
                continue

            with open(filepath, "rb") as f:
                img_bytes = f.read()

            try:
                res = EnrollmentService.direct_enroll_student(
                    db=db,
                    roll_number=roll,
                    full_name=name,
                    department="CIVIL",
                    academic_year="2026-2030 (First Year)",
                    institutional_email=email,
                    cohort_id=cohort.id,
                    file_bytes=img_bytes,
                )
                print(f"[{i+1}/{total}] OK: {roll} | {name:25s} | Models: {len(res.get('models_enrolled', []))} | Photo: {res.get('cloudinary_photo_url')[:60]}...")
                success_count += 1
            except Exception as e:
                print(f"[{i+1}/{total}] ERROR for {roll} ({name}): {e}")
                failed_count += 1

        print(f"\nEnrollment Complete: {success_count} succeeded, {skipped_count} skipped (already present), {failed_count} failed.")

    finally:
        db.close()


if __name__ == "__main__":
    roll_choice = 7
    if len(sys.argv) > 1:
        roll_choice = int(sys.argv[1])
    run_batch_enrollment(soundharya_roll=roll_choice)

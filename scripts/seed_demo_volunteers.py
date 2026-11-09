#!/usr/bin/env python3
"""
FRS V7.1 K² — Dedicated Demo Volunteer Offering Seeder.
Creates an isolated, controlled demo classroom offering and cohort for live presentation
with consented test identities and explicit non-biometric manual review cases.
"""

import sys
import uuid
from datetime import date
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
backend_dir = repo_root / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from app.core.database import SessionLocal
from app.domain.enums import UserRole, AcademicTerm, EnrollmentStatus
from app.domain.models.academic import (
    Department,
    Cohort,
    AcademicYear,
    Term,
    Subject,
    SubjectOffering,
    Faculty,
    FacultyAssignment,
)
from app.domain.models.student import Student, Enrollment, EnrollmentProfile


def seed_demo_environment():
    print("=== Seeding FRS V7.1 Controlled Live Demo Environment ===")
    with SessionLocal() as db:
        # 1. Fetch or create CSE department
        dept = db.execute(select(Department).where(Department.code == "CSE")).scalar_one_or_none()
        if not dept:
            dept = Department(id=str(uuid.uuid4()), code="CSE", name="Department of Computer Science & Engineering", is_active=True)
            db.add(dept)
            db.flush()

        # 2. Fetch or create Faculty Dr. Ramana
        fac = db.execute(select(Faculty).where(Faculty.employee_id == "KUCET-FAC-CSE-001")).scalar_one_or_none()
        if not fac:
            print("[INFO] Creating Faculty Dr. V. Ramana...")
            from app.domain.models.academic import User
            from app.core.security import hash_password
            u = User(
                id=str(uuid.uuid4()),
                email="ramana.vrb@gmail.com",
                hashed_password=hash_password("KucetFaculty@2026"),
                role=UserRole.FACULTY,
                is_active=True,
            )
            db.add(u)
            db.flush()
            fac = Faculty(
                id=str(uuid.uuid4()),
                user_id=u.id,
                employee_id="KUCET-FAC-CSE-001",
                full_name="Dr. V. Ramana",
                department_id=dept.id,
            )
            db.add(fac)
            db.flush()

        # 3. Academic Year & Term
        ay = db.execute(select(AcademicYear).where(AcademicYear.year_code == "2026-2027")).scalar_one_or_none()
        if not ay:
            ay = AcademicYear(id=str(uuid.uuid4()), year_code="2026-2027", start_date=date(2026, 8, 1), end_date=date(2027, 5, 31), is_current=True)
            db.add(ay)
            db.flush()

        term = db.execute(select(Term).where(Term.academic_year_id == ay.id, Term.term_type == AcademicTerm.ODD)).scalar_one_or_none()
        if not term:
            term = Term(id=str(uuid.uuid4()), academic_year_id=ay.id, term_type=AcademicTerm.ODD, start_date=date(2026, 8, 1), end_date=date(2026, 12, 31), is_current=True)
            db.add(term)
            db.flush()

        # 4. Demo Cohort
        cohort = db.execute(select(Cohort).where(Cohort.name == "Demo Cohort Class of 2026")).scalar_one_or_none()
        if not cohort:
            cohort = Cohort(id=str(uuid.uuid4()), department_id=dept.id, name="Demo Cohort Class of 2026", admission_year=2022, graduation_year=2026)
            db.add(cohort)
            db.flush()

        # 5. Demo Subject & Offering
        subj = db.execute(select(Subject).where(Subject.code == "CS401")).scalar_one_or_none()
        if not subj:
            subj = Subject(id=str(uuid.uuid4()), department_id=dept.id, code="CS401", name="Distributed Systems & Cloud Computing")
            db.add(subj)
            db.flush()

        off = db.execute(select(SubjectOffering).where(SubjectOffering.subject_id == subj.id, SubjectOffering.primary_cohort_id == cohort.id)).scalar_one_or_none()
        if not off:
            off = SubjectOffering(id=str(uuid.uuid4()), subject_id=subj.id, term_id=term.id, primary_cohort_id=cohort.id, section="DEMO", is_active=True)
            db.add(off)
            db.flush()
            asg = FacultyAssignment(id=str(uuid.uuid4()), faculty_id=fac.id, offering_id=off.id, is_active=True, start_date=term.start_date, end_date=term.end_date)
            db.add(asg)
            db.flush()

        # 6. Seed Consented Volunteer Students
        demo_students = [
            {"roll": "00622501", "name": "Katkam Koushik", "email": "00622501@kucet.ac.in", "consent": True},
            {"roll": "00622502", "name": "Volunteer Presenter", "email": "volunteer.a@kucet.ac.in", "consent": True},
            {"roll": "00622504", "name": "Ch. Rahul (Manual Review)", "email": "00622504@kucet.ac.in", "consent": False},
        ]

        for s_data in demo_students:
            stu = db.execute(select(Student).where(Student.roll_number == s_data["roll"])).scalar_one_or_none()
            if not stu:
                stu = Student(
                    id=str(uuid.uuid4()),
                    roll_number=s_data["roll"],
                    institutional_email=s_data["email"],
                    full_name=s_data["name"],
                    cohort_id=cohort.id,
                    is_active=True,
                )
                db.add(stu)
                db.flush()

            # Ensure enrollment in offering
            enr = db.execute(select(Enrollment).where(Enrollment.student_id == stu.id, Enrollment.offering_id == off.id)).scalar_one_or_none()
            if not enr:
                enr = Enrollment(
                    id=str(uuid.uuid4()),
                    student_id=stu.id,
                    offering_id=off.id,
                    effective_start=date(2022, 8, 1),
                    status=EnrollmentStatus.ACTIVE,
                )
                db.add(enr)
                db.flush()

        db.commit()
        print(f"[SUCCESS] Controlled demo environment successfully primed.")
        print(f"          Faculty     : Dr. V. Ramana (ramana.vrb@gmail.com)")
        print(f"          Offering    : CS401 Section DEMO ({off.id})")
        print(f"          Demo Roster : 3 students (including 1 consent-withheld manual check)")


if __name__ == "__main__":
    seed_demo_environment()

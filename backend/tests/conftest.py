"""
K² FRS — Test Suite Configuration & Fixtures.
Runs SQLite in-process in the system temp directory for 100% deterministic testing.
"""

from datetime import date, timedelta
import os
from pathlib import Path
import sys
import tempfile
import uuid

# Ensure backend root is in search path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

settings.ENVIRONMENT = "test"

from app.core.database import Base, get_db
from app.core.security import hash_password, create_access_token
from app.domain.enums import UserRole, AcademicTerm, EnrollmentStatus
from app.domain.models.academic import (
    User,
    Department,
    Cohort,
    AcademicYear,
    Term,
    Subject,
    SubjectOffering,
    Faculty,
    FacultyAssignment,
)
from app.domain.models.student import Student, Enrollment

test_db_file = Path(tempfile.gettempdir()) / f"pytest_frs_{uuid.uuid4().hex[:6]}.db"
engine = create_engine(f"sqlite:///{test_db_file.as_posix()}", connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture(scope="function")
def db_session():
    """Provides an isolated database session per test."""
    Base.metadata.create_all(engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def seed_data(db_session: Session):
    """Seeds baseline academic configuration: Admin, Faculty, Department, Cohort, Subject, Offering, Students."""
    today = date.today()

    # 1. Department
    dept = Department(code="CSE", name="Computer Science and Engineering")
    db_session.add(dept)
    db_session.flush()

    # 2. Admin & Faculty Users
    admin_user = User(
        email="admin@kucet.ac.in",
        hashed_password=hash_password("admin_pass_123"),
        role=UserRole.ADMIN,
        department_id=dept.id,
    )
    fac_user = User(
        email="shiva.faculty@kucet.ac.in",
        hashed_password=hash_password("faculty_pass_123"),
        role=UserRole.FACULTY,
        department_id=dept.id,
    )
    db_session.add_all([admin_user, fac_user])
    db_session.flush()

    # 3. Faculty Profile
    faculty = Faculty(
        user_id=fac_user.id,
        employee_id="FAC-CSE-001",
        full_name="Dr. Shiva Kumar",
        department_id=dept.id,
    )
    db_session.add(faculty)
    db_session.flush()

    # 3. Academic Year & Term
    ay = AcademicYear(year_code="2026-2027", start_date=today, end_date=today + timedelta(days=365), is_current=True)
    db_session.add(ay)
    db_session.flush()

    term = Term(academic_year_id=ay.id, term_type=AcademicTerm.ODD, start_date=today, end_date=today + timedelta(days=120))
    db_session.add(term)
    db_session.flush()

    # 4. Cohorts
    cohort1 = Cohort(department_id=dept.id, name="CSE-2023-2027", admission_year=2023, graduation_year=2027)
    cohort2 = Cohort(department_id=dept.id, name="CSD-2023-2027", admission_year=2023, graduation_year=2027)
    db_session.add_all([cohort1, cohort2])
    db_session.flush()

    # 5. Subject & Offering
    subject = Subject(code="CS301", name="Operating Systems", department_id=dept.id, credits=3)
    db_session.add(subject)
    db_session.flush()

    offering = SubjectOffering(
        subject_id=subject.id,
        term_id=term.id,
        primary_cohort_id=cohort1.id,
        section="A",
    )
    db_session.add(offering)
    db_session.flush()

    # 6. Faculty Assignment (Effective for today)
    assignment = FacultyAssignment(
        faculty_id=faculty.id,
        offering_id=offering.id,
        start_date=today - timedelta(days=30),
        end_date=today + timedelta(days=90),
        is_active=True,
    )
    db_session.add(assignment)

    # 7. Students & Enrollments
    s1 = Student(roll_number="23CSE01", full_name="Aarav Sharma", cohort_id=cohort1.id)
    s2 = Student(roll_number="23CSE02", full_name="Diya Patel", cohort_id=cohort1.id)
    s3 = Student(roll_number="23CSE03", full_name="Vikram Singh", cohort_id=cohort1.id)
    db_session.add_all([s1, s2, s3])
    db_session.flush()

    e1 = Enrollment(student_id=s1.id, offering_id=offering.id, status=EnrollmentStatus.ACTIVE, effective_start=today - timedelta(days=30))
    e2 = Enrollment(student_id=s2.id, offering_id=offering.id, status=EnrollmentStatus.ACTIVE, effective_start=today - timedelta(days=30))
    e3 = Enrollment(student_id=s3.id, offering_id=offering.id, status=EnrollmentStatus.ACTIVE, effective_start=today - timedelta(days=30))
    db_session.add_all([e1, e2, e3])

    db_session.commit()

    return {
        "admin_user": admin_user,
        "faculty_user": fac_user,
        "faculty": faculty,
        "department": dept,
        "cohort1": cohort1,
        "cohort2": cohort2,
        "offering": offering,
        "students": [s1, s2, s3],
    }

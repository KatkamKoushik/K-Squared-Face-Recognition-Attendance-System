"""
K² FRS — Academic Schema & Resource Authorization Tests.
"""

from datetime import date, timedelta
import pytest
from sqlalchemy.orm import Session
from app.core.errors import PermissionDeniedError
from app.domain.enums import UserRole
from app.domain.models.academic import User, Faculty
from app.core.security import hash_password
from app.services.academic_service import AcademicService


def test_faculty_assignment_verification_success(db_session: Session, seed_data):
    faculty = seed_data["faculty"]
    offering = seed_data["offering"]

    assignment = AcademicService.verify_faculty_assignment(
        db=db_session,
        faculty_id=faculty.id,
        offering_id=offering.id,
    )
    assert assignment is not None
    assert assignment.faculty_id == faculty.id
    assert assignment.offering_id == offering.id


def test_unassigned_faculty_rejected(db_session: Session, seed_data):
    """Negative test: faculty lacking assigned offering fails closed."""
    other_user = User(
        email="other.faculty@kucet.ac.in",
        hashed_password=hash_password("password"),
        role=UserRole.FACULTY,
    )
    db_session.add(other_user)
    db_session.flush()

    other_faculty = Faculty(
        user_id=other_user.id,
        employee_id="FAC-ECE-999",
        full_name="Prof. Other",
        department_id=seed_data["department"].id,
    )
    db_session.add(other_faculty)
    db_session.flush()

    offering = seed_data["offering"]

    with pytest.raises(PermissionDeniedError) as exc_info:
        AcademicService.verify_faculty_assignment(
            db=db_session,
            faculty_id=other_faculty.id,
            offering_id=offering.id,
        )
    assert exc_info.value.reason_code == "FACULTY_NOT_ASSIGNED"

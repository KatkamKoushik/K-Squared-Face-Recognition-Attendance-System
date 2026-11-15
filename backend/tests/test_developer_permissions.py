"""
K² FRS — Developer Permissions & Database Control Test Suite.
Verifies that:
1. koushikkatkam@gmail.com has full DEVELOPER privileges.
2. Only koushikkatkam@gmail.com / DEVELOPER can rewrite student names, roll numbers, and database records.
3. Only koushikkatkam@gmail.com / DEVELOPER can delete biometric photos and profiles from the database.
4. Non-developer accounts receive 403 Forbidden on these operations.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import SessionLocal
from app.core.security import create_access_token, hash_password
from app.domain.enums import UserRole
from app.domain.models.academic import User, Department, Cohort
from app.domain.models.student import Student, EnrollmentProfile

client = TestClient(app)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_koushikkatkam_developer_account_exists(db_session: Session):
    dev = db_session.query(User).filter(User.email == "koushikkatkam@gmail.com").first()
    assert dev is not None, "koushikkatkam@gmail.com must exist in database"
    assert dev.role == UserRole.DEVELOPER, "koushikkatkam@gmail.com must hold UserRole.DEVELOPER"
    assert dev.is_active is True, "koushikkatkam@gmail.com must be active"


def test_developer_can_update_student_details(db_session: Session):
    dev = db_session.query(User).filter(User.email == "koushikkatkam@gmail.com").first()
    token = create_access_token(subject=dev.email, role="DEVELOPER", additional_claims={"user_id": dev.id})
    headers = {"Authorization": f"Bearer {token}"}

    student = db_session.query(Student).first()
    assert student is not None, "At least one student must exist in database"
    original_name = student.full_name

    # Developer updates name
    res = client.patch(
        f"/api/v1/academic/students/{student.id}",
        headers=headers,
        json={"full_name": "Test Modified Name"},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["full_name"] == "Test Modified Name"

    # Restore original name
    res_restore = client.patch(
        f"/api/v1/academic/students/{student.id}",
        headers=headers,
        json={"full_name": original_name},
    )
    assert res_restore.status_code == 200
    assert res_restore.json()["data"]["full_name"] == original_name


def test_non_developer_forbidden_from_updating_student_details(db_session: Session):
    faculty = db_session.query(User).filter(User.role == UserRole.FACULTY).first()
    if not faculty:
        faculty = db_session.query(User).filter(User.role == UserRole.SUB_ADMIN).first()
    assert faculty is not None

    token = create_access_token(subject=faculty.email, role="FACULTY", additional_claims={"user_id": faculty.id})
    headers = {"Authorization": f"Bearer {token}"}

    student = db_session.query(Student).first()
    res = client.patch(
        f"/api/v1/academic/students/{student.id}",
        headers=headers,
        json={"full_name": "Unauthorized Hack Name"},
    )
    assert res.status_code == 403, f"Expected 403 Forbidden, got {res.status_code}"


def test_developer_can_delete_student_photo_and_profiles(db_session: Session):
    import uuid
    dev = db_session.query(User).filter(User.email == "koushikkatkam@gmail.com").first()
    token = create_access_token(subject=dev.email, role="DEVELOPER", additional_claims={"user_id": dev.id})
    headers = {"Authorization": f"Bearer {token}"}

    cohort = db_session.query(Cohort).first()
    assert cohort is not None

    # Create a temporary test student with profile to test deletion without touching real roster
    temp_id = str(uuid.uuid4())
    temp_student = Student(
        id=temp_id,
        roll_number=f"TEST_DEL_{temp_id[:6]}",
        full_name="Temp Delete Test Student",
        cohort_id=cohort.id,
        is_active=True,
    )
    db_session.add(temp_student)
    db_session.flush()

    temp_profile = EnrollmentProfile(
        id=str(uuid.uuid4()),
        student_id=temp_id,
        model_artifact_id="test_sha",
        embedding_namespace="sface_128d_v1",
        embedding_dimension=128,
        vector_data=[0.1] * 128,
        profile_version=1,
        is_active=True,
    )
    db_session.add(temp_profile)
    db_session.commit()

    # Non-developer delete attempt must fail with 403
    admin = db_session.query(User).filter(User.role == UserRole.ADMIN).first()
    if admin:
        admin_token = create_access_token(subject=admin.email, role="ADMIN", additional_claims={"user_id": admin.id})
        res_admin = client.delete(
            f"/api/v1/academic/students/{temp_id}/photo",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert res_admin.status_code == 403

    # Developer delete succeeds
    res = client.delete(
        f"/api/v1/academic/students/{temp_id}/photo",
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["success"] is True
    assert data["student_id"] == temp_id

    # Verify profiles for this test student are now 0
    remaining = db_session.query(EnrollmentProfile).filter(EnrollmentProfile.student_id == temp_id).count()
    assert remaining == 0, "Profiles must be deleted from database"

    # Clean up temp student
    db_session.delete(temp_student)
    db_session.commit()


def test_developer_can_delete_student_completely(db_session: Session):
    import uuid
    dev = db_session.query(User).filter(User.email == "koushikkatkam@gmail.com").first()
    token = create_access_token(subject=dev.email, role="DEVELOPER", additional_claims={"user_id": dev.id})
    headers = {"Authorization": f"Bearer {token}"}

    cohort = db_session.query(Cohort).first()
    assert cohort is not None

    temp_id = str(uuid.uuid4())
    temp_student = Student(
        id=temp_id,
        roll_number=f"TEST_STUD_DEL_{temp_id[:6]}",
        full_name="Temp Complete Delete Student",
        cohort_id=cohort.id,
        is_active=True,
    )
    db_session.add(temp_student)
    db_session.commit()

    # Non-developer delete attempt fails with 403
    admin = db_session.query(User).filter(User.role == UserRole.ADMIN).first()
    if admin:
        admin_token = create_access_token(subject=admin.email, role="ADMIN", additional_claims={"user_id": admin.id})
        res_admin = client.delete(
            f"/api/v1/academic/students/{temp_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert res_admin.status_code == 403

    # Developer delete succeeds
    res = client.delete(
        f"/api/v1/academic/students/{temp_id}",
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["data"]["success"] is True

    # Verify student is removed from database
    check = db_session.query(Student).filter(Student.id == temp_id).first()
    assert check is None, "Student must be completely deleted from database"

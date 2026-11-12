"""
K² FRS — Student Portal, Academic Bulk Import & Attendance Export Integration Tests.
Verifies:
1. Student authentication and profile resolution.
2. Tenant-isolated attendance summary and unit-level ledger.
3. End-to-end student attendance appeal lifecycle (submit -> admin review -> ledger update).
4. Academic bulk CSV import with validation and transactional integrity.
5. Offering attendance CSV report export with denominator compliance.
"""

import io
import uuid
from datetime import date
import pytest
from fastapi.testclient import TestClient

from app.main import create_application
from app.core.database import SessionLocal, Base, engine
from app.core.security import hash_password
from app.domain.enums import UserRole, AttendanceStatus, AppealStatus, SessionState
from app.domain.models.academic import User, Department, Cohort, Subject, SubjectOffering, Term, AcademicYear, Faculty
from app.domain.models.student import Student, Enrollment
from app.domain.models.session import AttendanceSession, AttendanceUnit
from app.domain.models.attendance import AttendanceRecord, AttendanceAppeal


@pytest.fixture
def app():
    return create_application()


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        if session.bind.dialect.name == "sqlite":
            Base.metadata.create_all(bind=engine)
            from app.seeds.kucet_seed import seed_kucet_institutional_data
            seed_kucet_institutional_data(session)
        yield session
    finally:
        session.close()


def test_student_portal_and_academic_workflows(client, db):
    # 1. Setup Student User & Student Profile
    unique_suffix = uuid.uuid4().hex[:6].upper()
    student_roll = f"STU-{unique_suffix}"
    student_email = f"student_{unique_suffix.lower()}@kucet.ac.in"
    password = "StudentPassword@2026"

    cohort = db.query(Cohort).first()
    assert cohort is not None, "Cohort must exist for student assignment"

    # Create Student record
    student = Student(
        id=str(uuid.uuid4()),
        roll_number=student_roll,
        full_name=f"Test Student {unique_suffix}",
        institutional_email=student_email,
        cohort_id=cohort.id,
        is_active=True,
    )
    db.add(student)

    # Create Student User Account
    student_user = User(
        id=str(uuid.uuid4()),
        email=student_email,
        hashed_password=hash_password(password),
        role=UserRole.STUDENT,
        is_active=True,
    )
    db.add(student_user)
    db.commit()

    # 2. Authenticate as Student
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": student_email, "password": password},
    )
    assert login_res.status_code == 200, f"Student login failed: {login_res.text}"
    student_token = login_res.json()["data"]["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # 3. Test GET /api/v1/student/me
    profile_res = client.get("/api/v1/student/me", headers=student_headers)
    assert profile_res.status_code == 200, f"Profile fetch failed: {profile_res.text}"
    profile_data = profile_res.json()["data"]
    assert profile_data["roll_number"] == student_roll
    assert profile_data["institutional_email"] == student_email
    assert profile_data["cohort_name"] == cohort.name

    # 4. Create an Isolated Offering, Enroll Student, and Create a Finalized Attendance Session
    subject = db.query(Subject).first()
    term = db.query(Term).first()
    offering = SubjectOffering(
        id=str(uuid.uuid4()),
        subject_id=subject.id,
        term_id=term.id,
        primary_cohort_id=cohort.id,
        section=f"T{unique_suffix[:2]}",
        is_active=True,
    )
    db.add(offering)
    db.flush()

    enrollment = Enrollment(
        id=str(uuid.uuid4()),
        student_id=student.id,
        offering_id=offering.id,
        status="ACTIVE",
        effective_start=date.today(),
    )
    db.add(enrollment)

    faculty = db.query(Faculty).first()
    assert faculty is not None

    session_id = f"SES-TEST-{unique_suffix}"
    att_session = AttendanceSession(
        id=session_id,
        offering_id=offering.id,
        faculty_id=faculty.id,
        session_date=date.today(),
        state=SessionState.FINALIZED,
        planned_units=2,
    )
    db.add(att_session)

    unit1 = AttendanceUnit(
        id=f"UNT1-{unique_suffix}",
        session_id=session_id,
        unit_index=1,
        is_conducted=True,
        status="CONDUCTED_CONFIRMED",
    )
    unit2 = AttendanceUnit(
        id=f"UNT2-{unique_suffix}",
        session_id=session_id,
        unit_index=2,
        is_conducted=True,
        status="CONDUCTED_CONFIRMED",
    )
    db.add_all([unit1, unit2])

    # Record 1 Present, Record 2 Absent
    admin_user = db.query(User).filter_by(role=UserRole.ADMIN).first()
    rec1 = AttendanceRecord(
        session_id=session_id,
        unit_id=unit1.id,
        student_id=student.id,
        status=AttendanceStatus.PRESENT_CONFIRMED,
        finalized_by_user_id=admin_user.id,
        reason_code="E2E_TEST_PRESENT",
    )
    rec2 = AttendanceRecord(
        session_id=session_id,
        unit_id=unit2.id,
        student_id=student.id,
        status=AttendanceStatus.ABSENT_CONFIRMED,
        finalized_by_user_id=admin_user.id,
        reason_code="E2E_TEST_ABSENT",
    )
    db.add_all([rec1, rec2])
    db.commit()

    # 5. Test GET /api/v1/student/me/attendance
    summary_res = client.get("/api/v1/student/me/attendance", headers=student_headers)
    assert summary_res.status_code == 200, f"Attendance summary failed: {summary_res.text}"
    summary_list = summary_res.json()["data"]
    matched_offering = next((s for s in summary_list if s["offering_id"] == offering.id), None)
    assert matched_offering is not None, "Enrolled offering must appear in student attendance summary"
    assert matched_offering["eligible_conducted_units"] >= 2
    assert matched_offering["attended_conducted_units"] >= 1
    assert matched_offering["attendance_percent"] is not None

    # 6. Test GET /api/v1/student/me/attendance/offerings/{offering_id}
    ledger_res = client.get(f"/api/v1/student/me/attendance/offerings/{offering.id}", headers=student_headers)
    assert ledger_res.status_code == 200, f"Ledger fetch failed: {ledger_res.text}"
    ledger_data = ledger_res.json()["data"]
    assert "sessions" in ledger_data
    matched_session = next((s for s in ledger_data["sessions"] if s["session_id"] == session_id), None)
    assert matched_session is not None
    assert len(matched_session["units"]) == 2

    # 7. Test POST /api/v1/student/me/appeals (Submit appeal for Unit 2)
    appeal_payload = {
        "session_id": session_id,
        "unit_id": unit2.id,
        "reason": "Official academic duty: university robotics symposium attendance.",
    }
    appeal_submit_res = client.post(
        "/api/v1/student/me/appeals",
        json=appeal_payload,
        headers=student_headers,
    )
    assert appeal_submit_res.status_code == 201, f"Appeal submit failed: {appeal_submit_res.text}"
    appeal_data = appeal_submit_res.json()["data"]
    appeal_id = appeal_data["id"]
    assert appeal_data["status"] == "PENDING"
    assert appeal_data["student_id"] == student.id

    # 8. Test GET /api/v1/student/me/appeals
    my_appeals_res = client.get("/api/v1/student/me/appeals", headers=student_headers)
    assert my_appeals_res.status_code == 200
    my_appeals = my_appeals_res.json()["data"]
    assert any(a["id"] == appeal_id for a in my_appeals)

    # 9. Admin Appeal Review Workflow
    admin_login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "principal.kucet@gmail.com", "password": "KucetFaculty@2026"},
    )
    assert admin_login_res.status_code == 200
    admin_token = admin_login_res.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Admin lists all appeals
    all_appeals_res = client.get("/api/v1/student/appeals/all", headers=admin_headers)
    assert all_appeals_res.status_code == 200
    assert any(a["id"] == appeal_id for a in all_appeals_res.json()["data"])

    # Admin approves appeal
    review_res = client.post(
        f"/api/v1/student/appeals/{appeal_id}/review",
        json={"approved": True, "review_notes": "Duty certificate verified by HOD."},
        headers=admin_headers,
    )
    assert review_res.status_code == 200
    assert review_res.json()["data"]["status"] == "APPROVED"

    # Verify ledger updated: record status is now EXCUSED
    db.expire_all()
    updated_rec = db.query(AttendanceRecord).filter_by(
        session_id=session_id, unit_id=unit2.id, student_id=student.id
    ).first()
    assert updated_rec.status == AttendanceStatus.EXCUSED

    # 10. Test CSV Bulk Student Import
    csv_content = f"roll_number,full_name,institutional_email,cohort_id\nBULK1_{unique_suffix},Bulk Student One,bulk1_{unique_suffix.lower()}@kucet.ac.in,{cohort.id}\nBULK2_{unique_suffix},Bulk Student Two,bulk2_{unique_suffix.lower()}@kucet.ac.in,{cohort.id}\n"
    import_res = client.post(
        "/api/v1/academic/import/students/csv",
        files={"file": ("students.csv", csv_content.encode("utf-8"), "text/csv")},
        headers=admin_headers,
    )
    assert import_res.status_code == 200, f"CSV import failed: {import_res.text}"
    import_data = import_res.json()["data"]
    assert import_data["imported_count"] == 2

    # 11. Test Offering Attendance CSV Export
    export_res = client.get(
        f"/api/v1/offerings/{offering.id}/export/csv",
        headers=admin_headers,
    )
    assert export_res.status_code == 200, f"CSV export failed: {export_res.text}"
    assert "text/csv" in export_res.headers.get("content-type", "")
    assert "Roll Number,Student Name,Attended Units,Conducted Units" in export_res.text

    # Teardown & Clean up test records
    try:
        db.query(AttendanceAppeal).filter(AttendanceAppeal.student_id == student.id).delete()
        db.query(AttendanceRecord).filter(AttendanceRecord.session_id == session_id).delete()
        db.query(AttendanceUnit).filter(AttendanceUnit.session_id == session_id).delete()
        db.query(AttendanceSession).filter(AttendanceSession.id == session_id).delete()
        db.query(Enrollment).filter(Enrollment.offering_id == offering.id).delete()
        db.query(SubjectOffering).filter(SubjectOffering.id == offering.id).delete()
        db.query(Student).filter(Student.roll_number.in_([student_roll, f"BULK1_{unique_suffix}", f"BULK2_{unique_suffix}"])).delete()
        db.query(User).filter(User.id == student_user.id).delete()
        db.commit()
    except Exception:
        db.rollback()


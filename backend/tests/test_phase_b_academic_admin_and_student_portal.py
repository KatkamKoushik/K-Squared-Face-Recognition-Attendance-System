"""
FRS V7.1 K² — Phase B Test Suite: Academic Administration, Cohort Rollover,
Student Lifecycle Management, Data Correction Workflows, and XLSX Attendance Export.
"""

from datetime import date, timedelta
import io
import uuid
import openpyxl
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.main import create_application
from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.domain.enums import UserRole, AcademicTerm, StudentLifecycleStatus, SessionState, AttendanceStatus
from app.domain.models.academic import (
    User,
    Department,
    Cohort,
    Subject,
    SubjectOffering,
    AcademicYear,
    Term,
    Faculty,
    FacultyAssignment,
)
from app.domain.models.student import Student, Enrollment, StudentDataCorrection
from app.domain.models.session import AttendanceSession, AttendanceUnit
from app.domain.models.attendance import AttendanceRecord
from app.domain.models.audit import CommitReceipt, AuditEvent


@pytest.fixture
def phase_b_env(db_session: Session):
    """Sets up a two-department academic structure with students, faculty, and offerings."""
    # Departments
    cse_dept = Department(id=str(uuid.uuid4()), code="CSE", name="Computer Science & Engineering", is_active=True)
    ece_dept = Department(id=str(uuid.uuid4()), code="ECE", name="Electronics & Communication Engineering", is_active=True)
    db_session.add_all([cse_dept, ece_dept])
    db_session.flush()

    # Cohorts
    cse_c1 = Cohort(id=str(uuid.uuid4()), department_id=cse_dept.id, name="CSE-2023-2027", admission_year=2023, graduation_year=2027, is_active=True)
    cse_c2 = Cohort(id=str(uuid.uuid4()), department_id=cse_dept.id, name="CSE-2024-2028", admission_year=2024, graduation_year=2028, is_active=True)
    ece_c1 = Cohort(id=str(uuid.uuid4()), department_id=ece_dept.id, name="ECE-2023-2027", admission_year=2023, graduation_year=2027, is_active=True)
    db_session.add_all([cse_c1, cse_c2, ece_c1])
    db_session.flush()

    # Academic Year & Term
    today = date.today()
    ay = AcademicYear(id=str(uuid.uuid4()), year_code="2026-2027", start_date=today, end_date=today + timedelta(days=365), is_current=True)
    db_session.add(ay)
    db_session.flush()

    term = Term(id=str(uuid.uuid4()), academic_year_id=ay.id, term_type=AcademicTerm.ODD, start_date=today, end_date=today + timedelta(days=120), is_active=True)
    db_session.add(term)
    db_session.flush()

    # Subjects
    cse_sub = Subject(id=str(uuid.uuid4()), code="CS401", name="Operating Systems", department_id=cse_dept.id, credits=4)
    ece_sub = Subject(id=str(uuid.uuid4()), code="EC401", name="Digital Signal Processing", department_id=ece_dept.id, credits=4)
    db_session.add_all([cse_sub, ece_sub])
    db_session.flush()

    # Subject Offerings
    cse_offering = SubjectOffering(id=str(uuid.uuid4()), subject_id=cse_sub.id, term_id=term.id, primary_cohort_id=cse_c1.id, section="A", is_active=True)
    ece_offering = SubjectOffering(id=str(uuid.uuid4()), subject_id=ece_sub.id, term_id=term.id, primary_cohort_id=ece_c1.id, section="A", is_active=True)
    db_session.add_all([cse_offering, ece_offering])
    db_session.flush()

    # Students
    stu1 = Student(
        id=str(uuid.uuid4()),
        roll_number="23CSE01",
        full_name="Aarav Sharma",
        institutional_email="aarav@kucet.ac.in",
        cohort_id=cse_c1.id,
        is_active=True,
        lifecycle_status=StudentLifecycleStatus.ACTIVE,
    )
    stu2 = Student(
        id=str(uuid.uuid4()),
        roll_number="23CSE02",
        full_name="Diya Patel",
        institutional_email="diya@kucet.ac.in",
        cohort_id=cse_c1.id,
        is_active=True,
        lifecycle_status=StudentLifecycleStatus.ACTIVE,
    )
    stu_ece = Student(
        id=str(uuid.uuid4()),
        roll_number="23ECE01",
        full_name="Rohan Reddy",
        institutional_email="rohan@kucet.ac.in",
        cohort_id=ece_c1.id,
        is_active=True,
        lifecycle_status=StudentLifecycleStatus.ACTIVE,
    )
    db_session.add_all([stu1, stu2, stu_ece])
    db_session.flush()

    # Enrollments
    enr1 = Enrollment(id=str(uuid.uuid4()), student_id=stu1.id, offering_id=cse_offering.id, status="ACTIVE", effective_start=today)
    enr2 = Enrollment(id=str(uuid.uuid4()), student_id=stu2.id, offering_id=cse_offering.id, status="ACTIVE", effective_start=today)
    db_session.add_all([enr1, enr2])
    db_session.flush()

    # Users
    super_admin = User(
        id=str(uuid.uuid4()),
        email="superadmin@kucet.ac.in",
        hashed_password=hash_password("adminpass"),
        role=UserRole.SUPER_ADMIN,
        is_active=True,
        token_version=1,
    )
    cse_admin = User(
        id=str(uuid.uuid4()),
        email="cse.admin@kucet.ac.in",
        hashed_password=hash_password("adminpass"),
        role=UserRole.ADMIN,
        department_id=cse_dept.id,
        is_active=True,
        token_version=1,
    )
    ece_admin = User(
        id=str(uuid.uuid4()),
        email="ece.admin@kucet.ac.in",
        hashed_password=hash_password("adminpass"),
        role=UserRole.ADMIN,
        department_id=ece_dept.id,
        is_active=True,
        token_version=1,
    )
    fac_user = User(
        id=str(uuid.uuid4()),
        email="prof.cse@kucet.ac.in",
        hashed_password=hash_password("facpass"),
        role=UserRole.FACULTY,
        department_id=cse_dept.id,
        is_active=True,
        token_version=1,
    )
    student_user = User(
        id=str(uuid.uuid4()),
        email="aarav@kucet.ac.in",
        hashed_password=hash_password("stupass"),
        role=UserRole.STUDENT,
        is_active=True,
        token_version=1,
    )
    db_session.add_all([super_admin, cse_admin, ece_admin, fac_user, student_user])
    db_session.flush()

    # Faculty Profile & Assignment
    faculty = Faculty(id=str(uuid.uuid4()), user_id=fac_user.id, employee_id="FAC-CSE-01", full_name="Dr. CSE Professor", department_id=cse_dept.id)
    db_session.add(faculty)
    db_session.flush()

    fac_assignment = FacultyAssignment(
        id=str(uuid.uuid4()),
        faculty_id=faculty.id,
        offering_id=cse_offering.id,
        start_date=today - timedelta(days=10),
        end_date=today + timedelta(days=90),
        is_active=True,
    )
    db_session.add(fac_assignment)
    db_session.flush()

    # Finalized Attendance Session & Units
    session = AttendanceSession(
        id=str(uuid.uuid4()),
        offering_id=cse_offering.id,
        faculty_id=faculty.id,
        session_date=today - timedelta(days=1),
        state=SessionState.FINALIZED,
        planned_units=2,
    )
    db_session.add(session)
    db_session.flush()

    u1 = AttendanceUnit(id=str(uuid.uuid4()), session_id=session.id, unit_index=1, is_conducted=True)
    u2 = AttendanceUnit(id=str(uuid.uuid4()), session_id=session.id, unit_index=2, is_conducted=True)
    db_session.add_all([u1, u2])
    db_session.flush()

    # Attendance Records
    r1 = AttendanceRecord(id=str(uuid.uuid4()), session_id=session.id, unit_id=u1.id, student_id=stu1.id, status=AttendanceStatus.PRESENT_CONFIRMED, finalized_by_user_id=fac_user.id)
    r2 = AttendanceRecord(id=str(uuid.uuid4()), session_id=session.id, unit_id=u2.id, student_id=stu1.id, status=AttendanceStatus.PRESENT_CONFIRMED, finalized_by_user_id=fac_user.id)
    r3 = AttendanceRecord(id=str(uuid.uuid4()), session_id=session.id, unit_id=u1.id, student_id=stu2.id, status=AttendanceStatus.PRESENT_CONFIRMED, finalized_by_user_id=fac_user.id)
    r4 = AttendanceRecord(id=str(uuid.uuid4()), session_id=session.id, unit_id=u2.id, student_id=stu2.id, status=AttendanceStatus.ABSENT_CONFIRMED, finalized_by_user_id=fac_user.id)
    db_session.add_all([r1, r2, r3, r4])

    receipt = CommitReceipt(
        id=str(uuid.uuid4()),
        session_id=session.id,
        idempotency_key="receipt-key-phase-b-test",
        committed_by_user_id=fac_user.id,
        total_conducted_units=2,
        total_present_records=3,
        total_absent_records=1,
        receipt_hash="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    )
    db_session.add(receipt)
    db_session.commit()

    return {
        "cse_dept": cse_dept,
        "ece_dept": ece_dept,
        "cse_c1": cse_c1,
        "cse_c2": cse_c2,
        "ece_c1": ece_c1,
        "ay": ay,
        "term": term,
        "cse_sub": cse_sub,
        "ece_sub": ece_sub,
        "cse_offering": cse_offering,
        "ece_offering": ece_offering,
        "stu1": stu1,
        "stu2": stu2,
        "stu_ece": stu_ece,
        "super_admin": super_admin,
        "cse_admin": cse_admin,
        "ece_admin": ece_admin,
        "fac_user": fac_user,
        "student_user": student_user,
        "session": session,
        "receipt": receipt,
    }


def make_client(db_session: Session, user: User) -> TestClient:
    app = create_application()
    app.dependency_overrides[get_db] = lambda: db_session
    claims = {
        "email": user.email,
        "department_id": user.department_id,
        "token_version": user.token_version,
    }
    token = create_access_token(
        subject=str(user.id),
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        additional_claims=claims,
    )
    client = TestClient(app)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


# ==============================================================================
# 1. Academic Administration Update Endpoints & RBAC
# ==============================================================================

def test_department_update_rbac(db_session: Session, phase_b_env: dict):
    """PUT /academic/departments/{id} permitted to SUPER_ADMIN, forbidden to department ADMIN."""
    super_client = make_client(db_session, phase_b_env["super_admin"])
    dept_id = phase_b_env["cse_dept"].id

    res = super_client.put(f"/api/v1/academic/departments/{dept_id}", json={"name": "CSE Advanced Department"})
    assert res.status_code == 200
    assert res.json()["data"]["name"] == "CSE Advanced Department"

    admin_client = make_client(db_session, phase_b_env["cse_admin"])
    res_forbidden = admin_client.put(f"/api/v1/academic/departments/{dept_id}", json={"name": "Hacked Name"})
    assert res_forbidden.status_code == 403


def test_cohort_update_department_isolation(db_session: Session, phase_b_env: dict):
    """PUT /academic/cohorts/{id} permits own department updates, rejects cross-department edits."""
    cse_client = make_client(db_session, phase_b_env["cse_admin"])
    cse_c1_id = phase_b_env["cse_c1"].id
    ece_c1_id = phase_b_env["ece_c1"].id

    # Own department edit succeeds
    res = cse_client.put(f"/api/v1/academic/cohorts/{cse_c1_id}", json={"name": "CSE-2023-Updated"})
    assert res.status_code == 200
    assert res.json()["data"]["name"] == "CSE-2023-Updated"

    # Cross-department edit rejected with 403
    res_cross = cse_client.put(f"/api/v1/academic/cohorts/{ece_c1_id}", json={"name": "ECE-Hacked"})
    assert res_cross.status_code == 403
    assert res_cross.json()["error"]["reason_code"] == "DEPARTMENT_ACCESS_RESTRICTED"


def test_academic_year_and_term_update(db_session: Session, phase_b_env: dict):
    """PUT /academic/academic-years/{id} and PUT /academic/terms/{id} guarded by SUPER_ADMIN."""
    super_client = make_client(db_session, phase_b_env["super_admin"])
    admin_client = make_client(db_session, phase_b_env["cse_admin"])

    ay_id = phase_b_env["ay"].id
    term_id = phase_b_env["term"].id

    # Admin forbidden
    assert admin_client.put(f"/api/v1/academic/academic-years/{ay_id}", json={"year_code": "2027-2028"}).status_code == 403
    assert admin_client.put(f"/api/v1/academic/terms/{term_id}", json={"is_active": False}).status_code == 403

    # Super admin succeeds
    res_ay = super_client.put(f"/api/v1/academic/academic-years/{ay_id}", json={"year_code": "2026-2027-Ext"})
    assert res_ay.status_code == 200
    assert res_ay.json()["data"]["year_code"] == "2026-2027-Ext"

    res_term = super_client.put(f"/api/v1/academic/terms/{term_id}", json={"is_active": True})
    assert res_term.status_code == 200


def test_subject_and_offering_update_isolation(db_session: Session, phase_b_env: dict):
    """PUT /academic/subjects/{id} and PUT /academic/offerings/{id} enforce department boundaries."""
    cse_client = make_client(db_session, phase_b_env["cse_admin"])
    cse_sub_id = phase_b_env["cse_sub"].id
    ece_sub_id = phase_b_env["ece_sub"].id
    cse_off_id = phase_b_env["cse_offering"].id
    ece_off_id = phase_b_env["ece_offering"].id

    # Own department updates succeed
    res_sub = cse_client.put(f"/api/v1/academic/subjects/{cse_sub_id}", json={"name": "Advanced OS", "credits": 4})
    assert res_sub.status_code == 200
    assert res_sub.json()["data"]["name"] == "Advanced OS"

    res_off = cse_client.put(f"/api/v1/academic/offerings/{cse_off_id}", json={"section": "B"})
    assert res_off.status_code == 200
    assert res_off.json()["data"]["section"] == "B"

    # Cross department updates fail
    assert cse_client.put(f"/api/v1/academic/subjects/{ece_sub_id}", json={"name": "Hijacked"}).status_code == 403
    assert cse_client.put(f"/api/v1/academic/offerings/{ece_off_id}", json={"section": "Z"}).status_code == 403


# ==============================================================================
# 2. Student Lifecycle Management & Cohort Rollover
# ==============================================================================

def test_student_lifecycle_transition_and_audit(db_session: Session, phase_b_env: dict):
    """PATCH /academic/students/{id}/lifecycle updates status and emits AuditEvent."""
    cse_client = make_client(db_session, phase_b_env["cse_admin"])
    stu1 = phase_b_env["stu1"]

    # Transition to ON_LEAVE
    res = cse_client.patch(
        f"/api/v1/academic/students/{stu1.id}/lifecycle",
        json={"status": "ON_LEAVE", "reason": "Medical leave approved by Dean"},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["lifecycle_status"] == "ON_LEAVE"
    assert data["is_active"] is False

    # Verify audit event logged
    audit = db_session.execute(
        select(AuditEvent).where(AuditEvent.action == "STUDENT_LIFECYCLE_UPDATED")
    ).scalar_one_or_none()
    assert audit is not None
    assert audit.before_state["lifecycle_status"] == "ACTIVE"
    assert audit.after_state["lifecycle_status"] == "ON_LEAVE"

    # Department isolation: CSE admin cannot alter ECE student
    ece_stu_id = phase_b_env["stu_ece"].id
    res_cross = cse_client.patch(
        f"/api/v1/academic/students/{ece_stu_id}/lifecycle",
        json={"status": "GRADUATED", "reason": "Unauthorized cross edit"},
    )
    assert res_cross.status_code == 403


def test_cohort_rollover_batch_promotion(db_session: Session, phase_b_env: dict):
    """POST /academic/cohorts/rollover moves active students from source to target cohort."""
    cse_client = make_client(db_session, phase_b_env["cse_admin"])
    cse_c1_id = phase_b_env["cse_c1"].id
    cse_c2_id = phase_b_env["cse_c2"].id
    ece_c1_id = phase_b_env["ece_c1"].id

    # Cross-department rollover forbidden
    res_cross = cse_client.post(
        "/api/v1/academic/cohorts/rollover",
        json={"from_cohort_id": cse_c1_id, "to_cohort_id": ece_c1_id, "reason": "Cross dept transfer"},
    )
    assert res_cross.status_code == 403

    # Within department rollover succeeds
    res_rollover = cse_client.post(
        "/api/v1/academic/cohorts/rollover",
        json={"from_cohort_id": cse_c1_id, "to_cohort_id": cse_c2_id, "reason": "Annual academic progression 2026"},
    )
    assert res_rollover.status_code == 200
    data = res_rollover.json()["data"]
    assert data["from_cohort_id"] == cse_c1_id
    assert data["to_cohort_id"] == cse_c2_id
    assert data["promoted_count"] >= 1

    # Verify audit event logged
    rollover_audit = db_session.execute(
        select(AuditEvent).where(AuditEvent.action == "COHORT_ROLLOVER_EXECUTED")
    ).scalar_one_or_none()
    assert rollover_audit is not None


# ==============================================================================
# 3. XLSX Attendance Export
# ==============================================================================

def test_export_offering_attendance_xlsx(db_session: Session, phase_b_env: dict):
    """GET /offerings/{id}/export/xlsx exports valid two-tab Excel spreadsheet."""
    fac_client = make_client(db_session, phase_b_env["fac_user"])
    offering_id = phase_b_env["cse_offering"].id

    res = fac_client.get(f"/api/v1/offerings/{offering_id}/export/xlsx")
    assert res.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in res.headers["content-type"]
    assert f'filename="attendance_{offering_id[:8]}.xlsx"' in res.headers["content-disposition"]

    # Validate workbook contents using openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(res.content))
    assert "Attendance Summary" in wb.sheetnames
    assert "Session Audit Trail" in wb.sheetnames

    ws_summary = wb["Attendance Summary"]
    assert ws_summary.cell(row=1, column=1).value == "Roll Number"
    assert ws_summary.cell(row=1, column=5).value == "Attendance Percentage"
    assert ws_summary.cell(row=1, column=6).value == "Institutional Status"

    # Verify student data present in sheet
    rolls = [ws_summary.cell(row=r, column=1).value for r in range(2, ws_summary.max_row + 1)]
    assert "23CSE01" in rolls

    ws_audit = wb["Session Audit Trail"]
    assert ws_audit.cell(row=1, column=1).value == "Session ID"
    assert ws_audit.cell(row=1, column=6).value == "Receipt Hash"


# ==============================================================================
# 4. Student Portal: Receipts in Ledger & Profile Lifecycle Status
# ==============================================================================

def test_student_profile_and_ledger_receipt_hash(db_session: Session, phase_b_env: dict):
    """Student profile reflects lifecycle status; ledger exposes cryptographic receipt hash."""
    student_client = make_client(db_session, phase_b_env["student_user"])
    offering_id = phase_b_env["cse_offering"].id

    # 1. Profile includes lifecycle_status
    res_prof = student_client.get("/api/v1/student/me")
    assert res_prof.status_code == 200
    prof = res_prof.json()["data"]
    assert prof["roll_number"] == "23CSE01"
    assert prof["lifecycle_status"] == "ACTIVE"

    # 2. Offering ledger includes receipt_hash for finalized session
    res_ledger = student_client.get(f"/api/v1/student/me/attendance/offerings/{offering_id}")
    assert res_ledger.status_code == 200
    ledger = res_ledger.json()["data"]
    assert len(ledger["sessions"]) > 0
    session_item = ledger["sessions"][0]
    assert session_item["receipt_hash"] is not None
    assert len(session_item["receipt_hash"]) == 64


# ==============================================================================
# 5. Student Data Correction Request & Administrative Review Lifecycle
# ==============================================================================

def test_student_data_correction_lifecycle(db_session: Session, phase_b_env: dict):
    """Student submits profile correction request; Admin reviews, approves, and updates profile."""
    student_client = make_client(db_session, phase_b_env["student_user"])
    cse_admin_client = make_client(db_session, phase_b_env["cse_admin"])

    # 1. Student submits request to correct misspelled name
    res_submit = student_client.post(
        "/api/v1/student/me/data-correction-request",
        json={
            "field_name": "full_name",
            "requested_value": "Aarav K. Sharma",
            "reason": "Name misspelled in original admission records",
        },
    )
    assert res_submit.status_code == 201
    corr_data = res_submit.json()["data"]
    assert corr_data["field_name"] == "full_name"
    assert corr_data["requested_value"] == "Aarav K. Sharma"
    assert corr_data["status"] == "PENDING"
    corr_id = corr_data["id"]

    # 2. Student lists their own requests
    res_list_student = student_client.get("/api/v1/student/me/data-correction-requests")
    assert res_list_student.status_code == 200
    req_ids = [r["id"] for r in res_list_student.json()["data"]]
    assert corr_id in req_ids

    # 3. Department Admin views pending requests
    res_admin_list = cse_admin_client.get("/api/v1/student/data-corrections/all?status_filter=PENDING")
    assert res_admin_list.status_code == 200
    admin_req_ids = [r["id"] for r in res_admin_list.json()["data"]]
    assert corr_id in admin_req_ids

    # 4. Department Admin reviews and approves request
    res_review = cse_admin_client.post(
        f"/api/v1/student/data-corrections/{corr_id}/review",
        json={"approved": True, "review_notes": "Verified against 10th standard mark sheet"},
    )
    assert res_review.status_code == 200
    reviewed_item = res_review.json()["data"]
    assert reviewed_item["status"] == "APPROVED"
    assert reviewed_item["review_notes"] == "Verified against 10th standard mark sheet"

    # 5. Verify Student profile in database was updated
    stu = db_session.get(Student, phase_b_env["stu1"].id)
    assert stu.full_name == "Aarav K. Sharma"

    # 6. Verify Audit Trail logged
    correction_audit = db_session.execute(
        select(AuditEvent).where(AuditEvent.action == "CORRECTION_PROCESSED")
    ).scalar_one_or_none()
    assert correction_audit is not None
    assert correction_audit.after_state["approved"] is True

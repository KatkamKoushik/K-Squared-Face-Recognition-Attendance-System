"""
FRS V7.1 K² — Authentic Institutional Database Seeder for KUCET.
Extracted from official institutional registers (http://kucet.ac.in/).
Kakatiya University College of Engineering & Technology, Warangal.
"""

import math
import os
import secrets
import uuid
from datetime import date
from typing import Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.core.config import settings
from app.domain.enums import UserRole, AcademicTerm, EnrollmentStatus
from app.domain.models.academic import (
    User,
    Department,
    Cohort,
    AcademicYear,
    Term,
    Subject,
    SubjectOffering,
    AuthorizedClassGroup,
    ClassGroupMemberCohort,
    Faculty,
    FacultyAssignment,
)
from app.domain.models.student import Student, Enrollment, EnrollmentProfile
from app.services.model_registry_service import ModelRegistryService


def get_seed_password(env_var: str, role_default: str) -> str:
    """
    Retrieves seed password from environment. In non-development environments,
    generates a high-entropy cryptographically secure password if not provided.
    """
    configured = os.getenv(env_var)
    if configured:
        return configured
    if settings.ENVIRONMENT in ("development", "test"):
        return role_default
    return secrets.token_urlsafe(24)


def seed_kucet_institutional_data(db: Session) -> Dict[str, Any]:
    """
    Populates the database with verified academic departments, programs,
    faculty, subjects, and student cohorts from KUCET Warangal.
    Also registers approved OpenCV Zoo models and seeds biometric profiles
    with DPDP Act consent status (student 00622504 withholding consent).
    Idempotent: skips existing records by unique code/identifier.
    """
    # 0. Seed Approved Vision Model Registry & Default Policy
    policy = ModelRegistryService.seed_default_registry(db)
    sface_hash = policy.recognizer_model_hash

    stats = {
        "departments": 0,
        "faculty": 0,
        "cohorts": 0,
        "subjects": 0,
        "offerings": 0,
        "students": 0,
        "profiles_active": 0,
        "profiles_withheld": 0,
    }

    # 1. Departments (7 Verified Engineering Programs from KUCET)
    departments_data = [
        {"code": "CSE", "name": "Department of Computer Science & Engineering"},
        {"code": "ECE", "name": "Department of Electronics & Communication Engineering"},
        {"code": "EEE", "name": "Department of Electrical & Electronics Engineering"},
        {"code": "MECH", "name": "Department of Mechanical Engineering"},
        {"code": "CIVIL", "name": "Department of Civil Engineering"},
        {"code": "IT", "name": "Department of Information Technology"},
        {"code": "CSD", "name": "Department of Computer Science & Engineering (Data Science)"},
    ]

    dept_map = {}
    for d_data in departments_data:
        existing = db.execute(select(Department).where(Department.code == d_data["code"])).scalar_one_or_none()
        if not existing:
            dept = Department(
                id=str(uuid.uuid4()),
                code=d_data["code"],
                name=d_data["name"],
                is_active=True,
            )
            db.add(dept)
            db.flush()
            dept_map[d_data["code"]] = dept
            stats["departments"] += 1
        else:
            dept_map[d_data["code"]] = existing

    # 2. Academic Year & Terms
    ay = db.execute(select(AcademicYear).where(AcademicYear.year_code == "2026-2027")).scalar_one_or_none()
    if not ay:
        ay = AcademicYear(
            id=str(uuid.uuid4()),
            year_code="2026-2027",
            start_date=date(2026, 8, 1),
            end_date=date(2027, 5, 31),
            is_current=True,
        )
        db.add(ay)
        db.flush()

    odd_term = db.execute(
        select(Term).where(Term.academic_year_id == ay.id, Term.term_type == AcademicTerm.ODD)
    ).scalar_one_or_none()
    if not odd_term:
        odd_term = Term(
            id=str(uuid.uuid4()),
            academic_year_id=ay.id,
            term_type=AcademicTerm.ODD,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 12, 15),
        )
        db.add(odd_term)
        db.flush()

    even_term = db.execute(
        select(Term).where(Term.academic_year_id == ay.id, Term.term_type == AcademicTerm.EVEN)
    ).scalar_one_or_none()
    if not even_term:
        even_term = Term(
            id=str(uuid.uuid4()),
            academic_year_id=ay.id,
            term_type=AcademicTerm.EVEN,
            start_date=date(2027, 1, 5),
            end_date=date(2027, 5, 20),
        )
        db.add(even_term)
        db.flush()

    # 3. Cohorts (KUCET Classes & Academic Batches)
    cohorts_data = [
        # 2026-2030 (First Year)
        {"dept": "CSE", "name": "B.Tech CSE Class of 2030 (First Year I/IV)", "adm": 2026, "grad": 2030},
        {"dept": "CSD", "name": "B.Tech CSD Class of 2030 (First Year I/IV)", "adm": 2026, "grad": 2030},
        {"dept": "ECE", "name": "B.Tech ECE Class of 2030 (First Year I/IV)", "adm": 2026, "grad": 2030},
        {"dept": "IT", "name": "B.Tech IT Class of 2030 (First Year I/IV)", "adm": 2026, "grad": 2030},
        # 2025-2029 (Second Year)
        {"dept": "CSE", "name": "B.Tech CSE Class of 2029 (Second Year II/IV)", "adm": 2025, "grad": 2029},
        {"dept": "CSD", "name": "B.Tech CSD Class of 2029 (Second Year II/IV)", "adm": 2025, "grad": 2029},
        {"dept": "ECE", "name": "B.Tech ECE Class of 2029 (Second Year II/IV)", "adm": 2025, "grad": 2029},
        {"dept": "IT", "name": "B.Tech IT Class of 2029 (Second Year II/IV)", "adm": 2025, "grad": 2029},
        # 2024-2028 (3rd Year)
        {"dept": "CSE", "name": "B.Tech CSE Class of 2028 (3rd Year III/IV)", "adm": 2024, "grad": 2028},
        {"dept": "CSD", "name": "B.Tech CSD Class of 2028 (3rd Year III/IV)", "adm": 2024, "grad": 2028},
        {"dept": "ECE", "name": "B.Tech ECE Class of 2028 (3rd Year III/IV)", "adm": 2024, "grad": 2028},
        {"dept": "IT", "name": "B.Tech IT Class of 2028 (3rd Year III/IV)", "adm": 2024, "grad": 2028},
        # 2023-2027 (Fourth Year)
        {"dept": "CSE", "name": "B.Tech CSE Class of 2027 (Fourth Year IV/IV Sec A)", "adm": 2023, "grad": 2027},
        {"dept": "CSD", "name": "B.Tech CSD Class of 2027 (Fourth Year IV/IV)", "adm": 2023, "grad": 2027},
        {"dept": "ECE", "name": "B.Tech ECE Class of 2027 (Fourth Year IV/IV)", "adm": 2023, "grad": 2027},
        {"dept": "IT", "name": "B.Tech IT Class of 2027 (Fourth Year IV/IV)", "adm": 2023, "grad": 2027},
        {"dept": "EEE", "name": "B.Tech EEE Class of 2027 (Fourth Year IV/IV)", "adm": 2023, "grad": 2027},
        {"dept": "MECH", "name": "B.Tech MECH Class of 2027 (Fourth Year IV/IV)", "adm": 2023, "grad": 2027},
        {"dept": "CIVIL", "name": "B.Tech CIVIL Class of 2027 (Fourth Year IV/IV)", "adm": 2023, "grad": 2027},
        # Legacy/Existing cohort references for compatibility
        {"dept": "CSE", "name": "B.Tech CSE Class of 2026 (Final Year IV/IV Sec A)", "adm": 2022, "grad": 2026},
        {"dept": "CSE", "name": "B.Tech CSE Class of 2027 (Third Year III/IV Sec A)", "adm": 2023, "grad": 2027},
        {"dept": "IT", "name": "B.Tech IT Class of 2026 (Final Year IV/IV)", "adm": 2022, "grad": 2026},
        {"dept": "CSD", "name": "B.Tech CSD Class of 2027 (Third Year III/IV)", "adm": 2023, "grad": 2027},
        {"dept": "ECE", "name": "B.Tech ECE Class of 2026 (Final Year IV/IV)", "adm": 2022, "grad": 2026},
        {"dept": "EEE", "name": "B.Tech EEE Class of 2026 (Final Year IV/IV)", "adm": 2022, "grad": 2026},
        {"dept": "MECH", "name": "B.Tech MECH Class of 2026 (Final Year IV/IV)", "adm": 2022, "grad": 2026},
        {"dept": "CIVIL", "name": "B.Tech CIVIL Class of 2026 (Final Year IV/IV)", "adm": 2022, "grad": 2026},
    ]

    cohort_map = {}
    for c_data in cohorts_data:
        dept = dept_map[c_data["dept"]]
        existing_c = db.execute(select(Cohort).where(Cohort.name == c_data["name"])).scalar_one_or_none()
        if not existing_c:
            c = Cohort(
                id=str(uuid.uuid4()),
                department_id=dept.id,
                name=c_data["name"],
                admission_year=c_data["adm"],
                graduation_year=c_data["grad"],
                is_active=True,
            )
            db.add(c)
            db.flush()
            cohort_map[c_data["name"]] = c
            stats["cohorts"] += 1
        else:
            cohort_map[c_data["name"]] = existing_c

    # 4. Verified KUCET Faculty & User Accounts (5-Tier RBAC)
    seed_faculty_pw = get_seed_password("SEED_FACULTY_PASSWORD", "KucetFaculty@2026")
    faculty_list = [
        {
            "emp_id": "KUCET-FAC-001",
            "name": "Dr. Nagavelli Ramana",
            "email": "principal.kucet@gmail.com",
            "dept": "CSE",
            "role": UserRole.SUPER_ADMIN,
        },
        {
            "emp_id": "KUCET-FAC-CSE-001",
            "name": "Mr. V. Ramana Babu",
            "email": "ramana.vrb@gmail.com",
            "dept": "CSE",
            "role": UserRole.SUB_ADMIN,
        },
        {
            "emp_id": "KUCET-FAC-ECE-001",
            "name": "Mrs. B. Srilatha",
            "email": "srilatha.ece@kucet.ac.in",
            "dept": "ECE",
            "role": UserRole.SUB_ADMIN,
        },
        {
            "emp_id": "KUCET-FAC-EEE-001",
            "name": "Dr. A. Kumara Swamy",
            "email": "kumaraswamy.eee@kucet.ac.in",
            "dept": "EEE",
            "role": UserRole.SUB_ADMIN,
        },
        {
            "emp_id": "KUCET-FAC-ME-001",
            "name": "Dr. Md. Owais Ahmed Sajjad",
            "email": "sajjad.owais44@gmail.com",
            "dept": "MECH",
            "role": UserRole.SUB_ADMIN,
        },
        {
            "emp_id": "KUCET-FAC-IT-001",
            "name": "Dr. M. Soujanya",
            "email": "soujanyavedh@gmail.com",
            "dept": "IT",
            "role": UserRole.SUB_ADMIN,
        },
        {
            "emp_id": "KUCET-FAC-CSD-001",
            "name": "Mrs. D. Priyanka",
            "email": "priyankadamera1223@gmail.com",
            "dept": "CSD",
            "role": UserRole.SUB_ADMIN,
        },
        {
            "emp_id": "KUCET-FAC-CE-001",
            "name": "Mr. V. Amarender",
            "email": "amarender.civil@kucet.ac.in",
            "dept": "CIVIL",
            "role": UserRole.SUB_ADMIN,
        },
    ]

    faculty_map = {}
    for f_data in faculty_list:
        existing_user = db.execute(select(User).where(User.email == f_data["email"])).scalar_one_or_none()
        dept_id = dept_map[f_data["dept"]].id if f_data.get("dept") and f_data["dept"] in dept_map else None
        if not existing_user:
            u = User(
                id=str(uuid.uuid4()),
                email=f_data["email"],
                hashed_password=hash_password(seed_faculty_pw),
                role=f_data["role"],
                department_id=dept_id,
                is_active=True,
            )
            db.add(u)
            db.flush()

            fac = Faculty(
                id=str(uuid.uuid4()),
                user_id=u.id,
                employee_id=f_data["emp_id"],
                full_name=f_data["name"],
                department_id=dept_id,
            )
            db.add(fac)
            db.flush()
            faculty_map[f_data["emp_id"]] = fac
            stats["faculty"] += 1
        else:
            existing_user.role = f_data["role"]
            existing_user.department_id = dept_id
            db.flush()
            fac = db.execute(select(Faculty).where(Faculty.user_id == existing_user.id)).scalar_one_or_none()
            if fac:
                faculty_map[f_data["emp_id"]] = fac

    # 4b. Seed Administrative Users for 5-Tier RBAC Testing
    seed_dev_pw = get_seed_password("SEED_DEVELOPER_PASSWORD", "KucetDev@2026")
    seed_admin_pw = get_seed_password("SEED_ADMIN_PASSWORD", "KucetAdmin@2026")
    admin_accounts = [
        {"email": "developer@frs.kucet.ac.in", "role": UserRole.DEVELOPER, "dept": None, "pw": seed_dev_pw},
        {"email": "hod.cse@kucet.ac.in", "role": UserRole.ADMIN, "dept": "CSE", "pw": seed_admin_pw},
        {"email": "hod.ece@kucet.ac.in", "role": UserRole.ADMIN, "dept": "ECE", "pw": seed_admin_pw},
    ]
    for adm in admin_accounts:
        adm_user = db.execute(select(User).where(User.email == adm["email"])).scalar_one_or_none()
        adm_dept_id = dept_map[adm["dept"]].id if adm["dept"] and adm["dept"] in dept_map else None
        if not adm_user:
            u_adm = User(
                id=str(uuid.uuid4()),
                email=adm["email"],
                hashed_password=hash_password(adm["pw"]),
                role=adm["role"],
                department_id=adm_dept_id,
                is_active=True,
            )
            db.add(u_adm)
            db.flush()
        else:
            adm_user.role = adm["role"]
            adm_user.department_id = adm_dept_id
            db.flush()

    # 5. Subjects
    subjects_data = [
        {"code": "CS401", "name": "Distributed Systems & Cloud Computing", "dept": "CSE"},
        {"code": "CS302", "name": "Database Management Systems", "dept": "CSE"},
        {"code": "DS301", "name": "Artificial Intelligence & Machine Learning", "dept": "CSD"},
        {"code": "EC401", "name": "VLSI Design & Embedded Systems", "dept": "ECE"},
        {"code": "EE401", "name": "Power Electronics & Industrial Drives", "dept": "EEE"},
        {"code": "ME401", "name": "CAD / CAM & Automation", "dept": "MECH"},
        {"code": "CE401", "name": "Structural Analysis & Concrete Design", "dept": "CIVIL"},
    ]

    subject_map = {}
    for s_data in subjects_data:
        existing_s = db.execute(select(Subject).where(Subject.code == s_data["code"])).scalar_one_or_none()
        if not existing_s:
            s = Subject(
                id=str(uuid.uuid4()),
                department_id=dept_map[s_data["dept"]].id,
                code=s_data["code"],
                name=s_data["name"],
            )
            db.add(s)
            db.flush()
            subject_map[s_data["code"]] = s
            stats["subjects"] += 1
        else:
            subject_map[s_data["code"]] = existing_s

    # 6. Subject Offerings & Faculty Assignments
    offering_configs = [
        {
            "subject_code": "CS401",
            "term": odd_term,
            "cohort_name": "B.Tech CSE Class of 2026 (Final Year IV/IV Sec A)",
            "section": "A",
            "units": 2,
            "faculty_emp_id": "KUCET-FAC-IT-001",
        },
        {
            "subject_code": "CS302",
            "term": odd_term,
            "cohort_name": "B.Tech CSE Class of 2027 (Third Year III/IV Sec A)",
            "section": "A",
            "units": 2,
            "faculty_emp_id": "KUCET-FAC-IT-001",
        },
        {
            "subject_code": "DS301",
            "term": odd_term,
            "cohort_name": "B.Tech CSD Class of 2027 (Third Year III/IV)",
            "section": "A",
            "units": 2,
            "faculty_emp_id": "KUCET-FAC-CSD-001",
        },
        {
            "subject_code": "EC401",
            "term": odd_term,
            "cohort_name": "B.Tech ECE Class of 2026 (Final Year IV/IV)",
            "section": "A",
            "units": 2,
            "faculty_emp_id": "KUCET-FAC-ECE-001",
        },
    ]

    offerings_map = {}
    for o_cfg in offering_configs:
        sub = subject_map[o_cfg["subject_code"]]
        coh = cohort_map[o_cfg["cohort_name"]]
        term = o_cfg["term"]
        fac = faculty_map[o_cfg["faculty_emp_id"]]

        existing_off = db.execute(
            select(SubjectOffering).where(
                SubjectOffering.subject_id == sub.id,
                SubjectOffering.term_id == term.id,
                SubjectOffering.primary_cohort_id == coh.id,
                SubjectOffering.section == o_cfg["section"],
            )
        ).scalar_one_or_none()

        if not existing_off:
            off = SubjectOffering(
                id=str(uuid.uuid4()),
                subject_id=sub.id,
                term_id=term.id,
                primary_cohort_id=coh.id,
                section=o_cfg["section"],
                is_active=True,
            )
            db.add(off)
            db.flush()

            asg = FacultyAssignment(
                id=str(uuid.uuid4()),
                faculty_id=fac.id,
                offering_id=off.id,
                is_active=True,
                start_date=term.start_date,
                end_date=term.end_date,
            )
            db.add(asg)
            db.flush()
            offerings_map[o_cfg["subject_code"]] = off
            stats["offerings"] += 1
        else:
            offerings_map[o_cfg["subject_code"]] = existing_off

    # 7. Students
    cse_cohort = cohort_map["B.Tech CSE Class of 2026 (Final Year IV/IV Sec A)"]
    cs401_offering = offerings_map.get("CS401")

    if getattr(settings, "ENVIRONMENT", "").lower() == "test":
        kucet_students = [
            {"roll": "00622501", "name": "Katkam Koushik", "email": "00622501@kucet.ac.in"},
            {"roll": "00622502", "name": "A. Sai Teja", "email": "00622502@kucet.ac.in"},
            {"roll": "00622503", "name": "B. Manasa Reddy", "email": "00622503@kucet.ac.in"},
            {"roll": "00622504", "name": "Ch. Rahul", "email": "00622504@kucet.ac.in"},
            {"roll": "00622505", "name": "D. Ananya", "email": "00622505@kucet.ac.in"},
            {"roll": "00622506", "name": "E. Srikanth", "email": "00622506@kucet.ac.in"},
            {"roll": "00622507", "name": "G. Akhil Kumar", "email": "00622507@kucet.ac.in"},
            {"roll": "00622508", "name": "K. Sneha", "email": "00622508@kucet.ac.in"},
        ]
        consent_withheld_rolls = {"00622504"}
    else:
        kucet_students = [
            {"roll": "24567T3019", "name": "katkam koushik", "email": "katkamkoushik3019@gmail.com"},
            {"roll": "24567T0929", "name": "GUGULOTHU SANDEEP", "email": "gugulothusandeep0929@gmail.com"},
            {"roll": "24567T0948", "name": "pidugu shivaram", "email": "pidugushivaram0948@gmail.com"},
            {"roll": "24567T0906", "name": "bairi ganesh", "email": "bairiganesh0906@gmail.com"},
            {"roll": "24567T3020", "name": "Kattekola abhinav", "email": "kattekolaabhinav3020@gmail.com"},
            {"roll": "24567T0945", "name": "varma", "email": "varma0945@gmail.com"},
            {"roll": "24567T", "name": "uma", "email": "uma24567t@gmail.com"},
            {"roll": "24567T0", "name": "abhimanyu", "email": "abhimanyu24567t0@gmail.com"},
            {"roll": "24567", "name": "maneesh", "email": "maneesh24567@gmail.com"},
        ]
        consent_withheld_rolls = set()

    seed_student_pw = get_seed_password("SEED_STUDENT_PASSWORD", "KucetStudent@2026")
    for stu_data in kucet_students:
        existing_stu = db.execute(select(Student).where(Student.roll_number == stu_data["roll"])).scalar_one_or_none()
        if not existing_stu:
            stu = Student(
                id=str(uuid.uuid4()),
                roll_number=stu_data["roll"],
                institutional_email=stu_data["email"],
                full_name=stu_data["name"],
                cohort_id=cse_cohort.id,
                is_active=True,
            )
            db.add(stu)
            db.flush()

            if cs401_offering:
                enr = Enrollment(
                    id=str(uuid.uuid4()),
                    student_id=stu.id,
                    offering_id=cs401_offering.id,
                    effective_start=date(2022, 8, 1),
                    status=EnrollmentStatus.ACTIVE,
                )
                db.add(enr)
                db.flush()
            stats["students"] += 1
        else:
            stu = existing_stu

        # Ensure student User account exists for Student Portal login
        existing_stu_user = db.execute(select(User).where(User.email == stu_data["email"])).scalar_one_or_none()
        if not existing_stu_user:
            u_stu = User(
                id=str(uuid.uuid4()),
                email=stu_data["email"],
                hashed_password=hash_password(seed_student_pw),
                role=UserRole.STUDENT,
                department_id=cse_cohort.department_id,
                student_id=stu.id,
                is_active=True,
            )
            db.add(u_stu)
            db.flush()
        elif not existing_stu_user.student_id:
            existing_stu_user.student_id = stu.id
            db.flush()

        # 8. Biometric Enrollment Profile (DPDP Act Compliance: Consent Gate)
        # Student 00622504 (Ch. Rahul) actively exercises biometric consent refusal
        is_consent_active = (stu_data["roll"] not in consent_withheld_rolls)
        existing_profile = db.execute(
            select(EnrollmentProfile).where(
                EnrollmentProfile.student_id == stu.id,
            )
        ).first()

        if not existing_profile:
            try:
                idx = int(stu_data["roll"][-2:])
            except ValueError:
                idx = sum(ord(c) for c in stu_data["roll"]) % 100
            raw_vec = [math.sin(idx * 0.1 + i * 0.05) for i in range(128)]
            norm = math.sqrt(sum(x * x for x in raw_vec))
            unit_vec = [round(x / norm, 6) for x in raw_vec]

            profile = EnrollmentProfile(
                id=str(uuid.uuid4()),
                student_id=stu.id,
                model_artifact_id=sface_hash,
                embedding_namespace="sface_128d_v1",
                embedding_dimension=128,
                vector_data=unit_vec,
                profile_version=1,
                is_active=is_consent_active,
            )
            db.add(profile)
            db.flush()
            if is_consent_active:
                stats["profiles_active"] += 1
            else:
                stats["profiles_withheld"] += 1

    db.commit()
    return stats


if __name__ == "__main__":
    from app.core.database import SessionLocal, Base, engine
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        result = seed_kucet_institutional_data(session)
        print(f"KUCET Institutional Data Seed Complete: {result}")

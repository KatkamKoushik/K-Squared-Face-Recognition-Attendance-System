"""
FRS V7.1 K² — Academic Administration Endpoints.
Guarded by ADMIN role. Configuration is represented as data, not code branches.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user, require_roles, get_correlation_id
from app.core.database import get_db
from app.domain.enums import UserRole
from app.domain.models.academic import User
from app.schemas.academic import (
    DepartmentCreate,
    DepartmentResponse,
    CohortCreate,
    CohortResponse,
    AcademicYearCreate,
    AcademicYearResponse,
    TermCreate,
    TermResponse,
    SubjectCreate,
    SubjectResponse,
    SubjectOfferingCreate,
    SubjectOfferingResponse,
    AuthorizedClassGroupCreate,
    AuthorizedClassGroupResponse,
    FacultyAssignmentCreate,
    FacultyAssignmentResponse,
    StudentCreate,
    StudentResponse,
    EnrollmentCreate,
    EnrollmentResponse,
)
from app.schemas.common import ResponseEnvelope
from app.services.academic_service import AcademicService

router = APIRouter(prefix="/academic", tags=["Academic Administration"])


@router.post("/departments", response_model=ResponseEnvelope[DepartmentResponse], status_code=status.HTTP_201_CREATED)
def create_department(
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    admin_user=Depends(require_roles([UserRole.ADMIN])),
    correlation_id: str = Depends(get_correlation_id),
):
    dept = AcademicService.create_department(db, data)
    return ResponseEnvelope(data=DepartmentResponse.model_validate(dept), correlation_id=correlation_id)


@router.get("/departments", response_model=ResponseEnvelope[List[DepartmentResponse]])
def list_departments(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id),
):
    depts = AcademicService.get_departments(db)
    items = [DepartmentResponse.model_validate(d) for d in depts]
    return ResponseEnvelope(data=items, correlation_id=correlation_id)


@router.post("/cohorts", response_model=ResponseEnvelope[CohortResponse], status_code=status.HTTP_201_CREATED)
def create_cohort(
    data: CohortCreate,
    db: Session = Depends(get_db),
    admin_user=Depends(require_roles([UserRole.ADMIN])),
    correlation_id: str = Depends(get_correlation_id),
):
    cohort = AcademicService.create_cohort(db, data)
    return ResponseEnvelope(data=CohortResponse.model_validate(cohort), correlation_id=correlation_id)


@router.get("/cohorts", response_model=ResponseEnvelope[List[CohortResponse]])
def list_cohorts(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id),
):
    cohorts = AcademicService.get_cohorts(db)
    items = [CohortResponse.model_validate(c) for c in cohorts]
    return ResponseEnvelope(data=items, correlation_id=correlation_id)


@router.post("/academic-years", response_model=ResponseEnvelope[AcademicYearResponse], status_code=status.HTTP_201_CREATED)
def create_academic_year(
    data: AcademicYearCreate,
    db: Session = Depends(get_db),
    admin_user=Depends(require_roles([UserRole.ADMIN])),
    correlation_id: str = Depends(get_correlation_id),
):
    ay = AcademicService.create_academic_year(db, data)
    return ResponseEnvelope(data=AcademicYearResponse.model_validate(ay), correlation_id=correlation_id)


@router.get("/academic-years", response_model=ResponseEnvelope[List[AcademicYearResponse]])
def list_academic_years(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id),
):
    years = AcademicService.get_academic_years(db)
    items = [AcademicYearResponse.model_validate(y) for y in years]
    return ResponseEnvelope(data=items, correlation_id=correlation_id)


@router.post("/terms", response_model=ResponseEnvelope[TermResponse], status_code=status.HTTP_201_CREATED)
def create_term(
    data: TermCreate,
    db: Session = Depends(get_db),
    admin_user=Depends(require_roles([UserRole.ADMIN])),
    correlation_id: str = Depends(get_correlation_id),
):
    term = AcademicService.create_term(db, data)
    return ResponseEnvelope(data=TermResponse.model_validate(term), correlation_id=correlation_id)


@router.get("/terms", response_model=ResponseEnvelope[List[TermResponse]])
def list_terms(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id),
):
    terms = AcademicService.get_terms(db)
    items = [TermResponse.model_validate(t) for t in terms]
    return ResponseEnvelope(data=items, correlation_id=correlation_id)


@router.post("/subjects", response_model=ResponseEnvelope[SubjectResponse], status_code=status.HTTP_201_CREATED)
def create_subject(
    data: SubjectCreate,
    db: Session = Depends(get_db),
    admin_user=Depends(require_roles([UserRole.ADMIN])),
    correlation_id: str = Depends(get_correlation_id),
):
    subject = AcademicService.create_subject(db, data)
    return ResponseEnvelope(data=SubjectResponse.model_validate(subject), correlation_id=correlation_id)


@router.get("/subjects", response_model=ResponseEnvelope[List[SubjectResponse]])
def list_subjects(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id),
):
    subjects = AcademicService.get_subjects(db)
    items = [SubjectResponse.model_validate(s) for s in subjects]
    return ResponseEnvelope(data=items, correlation_id=correlation_id)


@router.post("/offerings", response_model=ResponseEnvelope[SubjectOfferingResponse], status_code=status.HTTP_201_CREATED)
def create_offering(
    data: SubjectOfferingCreate,
    db: Session = Depends(get_db),
    admin_user=Depends(require_roles([UserRole.ADMIN])),
    correlation_id: str = Depends(get_correlation_id),
):
    offering = AcademicService.create_offering(db, data)
    return ResponseEnvelope(data=SubjectOfferingResponse.model_validate(offering), correlation_id=correlation_id)


@router.get("/offerings", response_model=ResponseEnvelope[List[SubjectOfferingResponse]])
def list_offerings(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id),
):
    from app.domain.models.academic import Cohort, Faculty, FacultyAssignment, Subject
    from app.domain.models.student import Student

    offerings = AcademicService.get_offerings(db)

    # If the user is a faculty member, filter to their actively assigned offerings
    if current_user.role == UserRole.FACULTY or str(current_user.role) == "FACULTY":
        faculty = db.query(Faculty).filter_by(user_id=current_user.id).first()
        if faculty:
            assigned_offering_ids = {
                a.offering_id for a in faculty.assignments if a.is_active
            }
            if assigned_offering_ids:
                offerings = [o for o in offerings if o.id in assigned_offering_ids]

    subject_map = {s.id: s for s in db.query(Subject).all()}
    cohort_map = {c.id: c for c in db.query(Cohort).all()}

    items = []
    for o in offerings:
        sub = subject_map.get(o.subject_id)
        coh = cohort_map.get(o.primary_cohort_id)
        sub_name = sub.name if sub else "Subject Offering"
        sub_code = sub.code if sub else ""
        cohort_name = coh.name if coh else "Active Cohort"
        student_count = db.query(Student).filter_by(cohort_id=o.primary_cohort_id).count() if coh else 0

        item = SubjectOfferingResponse(
            id=o.id,
            subject_id=o.subject_id,
            term_id=o.term_id,
            primary_cohort_id=o.primary_cohort_id,
            section=o.section,
            is_active=o.is_active,
            subject_code=sub_code,
            subject_name=sub_name,
            subjectName=f"{sub_name} ({sub_code})" if sub_code else sub_name,
            cohort_name=cohort_name,
            cohort=cohort_name,
            enrolled_count=student_count,
            enrolledCount=student_count,
        )
        items.append(item)

    return ResponseEnvelope(data=items, correlation_id=correlation_id)


@router.post("/groups", response_model=ResponseEnvelope[AuthorizedClassGroupResponse], status_code=status.HTTP_201_CREATED)
def create_authorized_group(
    data: AuthorizedClassGroupCreate,
    db: Session = Depends(get_db),
    admin_user=Depends(require_roles([UserRole.ADMIN])),
    correlation_id: str = Depends(get_correlation_id),
):
    group = AcademicService.create_authorized_group(db, data)
    res = AuthorizedClassGroupResponse(
        id=group.id,
        offering_id=group.offering_id,
        group_name=group.group_name,
        is_active=group.is_active,
        member_cohort_ids=data.cohort_ids,
    )
    return ResponseEnvelope(data=res, correlation_id=correlation_id)


@router.get("/groups", response_model=ResponseEnvelope[List[AuthorizedClassGroupResponse]])
def list_authorized_groups(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id),
):
    groups = AcademicService.get_groups(db)
    items = [
        AuthorizedClassGroupResponse(
            id=g.id,
            offering_id=g.offering_id,
            group_name=g.group_name,
            is_active=g.is_active,
            member_cohort_ids=[m.cohort_id for m in g.member_cohorts],
        )
        for g in groups
    ]
    return ResponseEnvelope(data=items, correlation_id=correlation_id)


@router.post("/faculty-assignments", response_model=ResponseEnvelope[FacultyAssignmentResponse], status_code=status.HTTP_201_CREATED)
def assign_faculty(
    data: FacultyAssignmentCreate,
    db: Session = Depends(get_db),
    admin_user=Depends(require_roles([UserRole.ADMIN])),
    correlation_id: str = Depends(get_correlation_id),
):
    assignment = AcademicService.assign_faculty(db, data)
    return ResponseEnvelope(data=FacultyAssignmentResponse.model_validate(assignment), correlation_id=correlation_id)


@router.get("/faculty-assignments", response_model=ResponseEnvelope[List[FacultyAssignmentResponse]])
def list_faculty_assignments(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id),
):
    assignments = AcademicService.get_faculty_assignments(db)
    items = [FacultyAssignmentResponse.model_validate(a) for a in assignments]
    return ResponseEnvelope(data=items, correlation_id=correlation_id)


@router.post("/students", response_model=ResponseEnvelope[StudentResponse], status_code=status.HTTP_201_CREATED)
def create_student(
    data: StudentCreate,
    db: Session = Depends(get_db),
    admin_user=Depends(require_roles([UserRole.ADMIN])),
    correlation_id: str = Depends(get_correlation_id),
):
    student = AcademicService.create_student(db, data)
    return ResponseEnvelope(data=StudentResponse.model_validate(student), correlation_id=correlation_id)


@router.get("/students", response_model=ResponseEnvelope[List[StudentResponse]])
def list_students(
    cohort_id: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id),
):
    """
    Lists students with strict object-level authorization:
    - Admin: institutional scope across all cohorts.
    - Faculty: scoped only to students in cohorts or enrollments assigned to the instructor.
    """
    students = AcademicService.get_students_scoped(
        db=db,
        user=current_user,
        cohort_id=cohort_id,
        limit=limit,
    )
    items = [StudentResponse.model_validate(s) for s in students]
    return ResponseEnvelope(data=items, correlation_id=correlation_id)


@router.post("/enrollments", response_model=ResponseEnvelope[EnrollmentResponse], status_code=status.HTTP_201_CREATED)
def enroll_student(
    data: EnrollmentCreate,
    db: Session = Depends(get_db),
    admin_user=Depends(require_roles([UserRole.ADMIN])),
    correlation_id: str = Depends(get_correlation_id),
):
    enrollment = AcademicService.enroll_student(db, data)
    return ResponseEnvelope(data=EnrollmentResponse.model_validate(enrollment), correlation_id=correlation_id)


@router.post("/seed-kucet", response_model=ResponseEnvelope[dict], status_code=status.HTTP_200_OK)
def seed_kucet(
    db: Session = Depends(get_db),
    admin_user=Depends(require_roles([UserRole.ADMIN])),
    correlation_id: str = Depends(get_correlation_id),
):
    from app.seeds.kucet_seed import seed_kucet_institutional_data
    stats = seed_kucet_institutional_data(db)
    return ResponseEnvelope(data=stats, correlation_id=correlation_id)


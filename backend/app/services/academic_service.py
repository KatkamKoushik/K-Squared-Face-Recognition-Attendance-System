"""
FRS V7.1 K² — Academic Administration & Eligibility Service.
"""

from datetime import date
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from app.core.errors import PermissionDeniedError, ResourceNotFoundError
from app.domain.enums import EnrollmentStatus
from app.domain.models.academic import (
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
from app.domain.models.student import Student, Enrollment
from app.schemas.academic import (
    DepartmentCreate,
    CohortCreate,
    AcademicYearCreate,
    TermCreate,
    SubjectCreate,
    SubjectOfferingCreate,
    AuthorizedClassGroupCreate,
    FacultyAssignmentCreate,
    StudentCreate,
    EnrollmentCreate,
)


class AcademicService:

    @staticmethod
    def create_department(db: Session, data: DepartmentCreate) -> Department:
        dept = Department(code=data.code.upper(), name=data.name)
        db.add(dept)
        db.flush()
        return dept

    @staticmethod
    def get_departments(db: Session) -> List[Department]:
        result = db.execute(select(Department).order_by(Department.code))
        return list(result.scalars().all())

    @staticmethod
    def create_cohort(db: Session, data: CohortCreate) -> Cohort:
        cohort = Cohort(**data.model_dump())
        db.add(cohort)
        db.flush()
        return cohort

    @staticmethod
    def get_cohorts(db: Session) -> List[Cohort]:
        result = db.execute(select(Cohort).order_by(Cohort.name))
        return list(result.scalars().all())

    @staticmethod
    def create_academic_year(db: Session, data: AcademicYearCreate) -> AcademicYear:
        year = AcademicYear(**data.model_dump())
        db.add(year)
        db.flush()
        return year

    @staticmethod
    def get_academic_years(db: Session) -> List[AcademicYear]:
        result = db.execute(select(AcademicYear).order_by(AcademicYear.name.desc()))
        return list(result.scalars().all())

    @staticmethod
    def create_term(db: Session, data: TermCreate) -> Term:
        term = Term(**data.model_dump())
        db.add(term)
        db.flush()
        return term

    @staticmethod
    def get_terms(db: Session) -> List[Term]:
        result = db.execute(select(Term).order_by(Term.start_date.desc()))
        return list(result.scalars().all())

    @staticmethod
    def create_subject(db: Session, data: SubjectCreate) -> Subject:
        subject = Subject(
            code=data.code.upper(),
            name=data.name,
            department_id=data.department_id,
            credits=data.credits,
        )
        db.add(subject)
        db.flush()
        return subject

    @staticmethod
    def get_subjects(db: Session) -> List[Subject]:
        result = db.execute(select(Subject).order_by(Subject.code))
        return list(result.scalars().all())

    @staticmethod
    def create_offering(db: Session, data: SubjectOfferingCreate) -> SubjectOffering:
        offering = SubjectOffering(**data.model_dump())
        db.add(offering)
        db.flush()
        return offering

    @staticmethod
    def get_offerings(db: Session) -> List[SubjectOffering]:
        result = db.execute(select(SubjectOffering).order_by(SubjectOffering.id.desc()))
        return list(result.scalars().all())

    @staticmethod
    def create_authorized_group(db: Session, data: AuthorizedClassGroupCreate) -> AuthorizedClassGroup:
        group = AuthorizedClassGroup(
            offering_id=data.offering_id,
            group_name=data.group_name,
        )
        db.add(group)
        db.flush()

        for c_id in data.cohort_ids:
            member = ClassGroupMemberCohort(group_id=group.id, cohort_id=c_id)
            db.add(member)
        db.flush()
        return group

    @staticmethod
    def get_groups(db: Session) -> List[AuthorizedClassGroup]:
        result = db.execute(select(AuthorizedClassGroup).order_by(AuthorizedClassGroup.group_name))
        return list(result.scalars().all())

    @staticmethod
    def assign_faculty(db: Session, data: FacultyAssignmentCreate) -> FacultyAssignment:
        assignment = FacultyAssignment(**data.model_dump())
        db.add(assignment)
        db.flush()
        return assignment

    @staticmethod
    def get_faculty_assignments(db: Session) -> List[FacultyAssignment]:
        result = db.execute(select(FacultyAssignment).order_by(FacultyAssignment.start_date.desc()))
        return list(result.scalars().all())

    @staticmethod
    def verify_faculty_assignment(
        db: Session,
        faculty_id: str,
        offering_id: str,
        class_group_id: Optional[str] = None,
        check_date: Optional[date] = None,
    ) -> FacultyAssignment:
        """
        Server-side authorization invariant:
        Validates faculty is actively assigned to the offering/group on check_date.
        """
        target_date = check_date or date.today()
        stmt = select(FacultyAssignment).where(
            and_(
                FacultyAssignment.faculty_id == faculty_id,
                FacultyAssignment.offering_id == offering_id,
                FacultyAssignment.is_active == True,
                FacultyAssignment.start_date <= target_date,
                FacultyAssignment.end_date >= target_date,
            )
        )
        if class_group_id:
            stmt = stmt.where(FacultyAssignment.class_group_id == class_group_id)

        result = db.execute(stmt)
        assignment = result.scalar_one_or_none()
        if not assignment:
            raise PermissionDeniedError(
                message="Faculty member does not possess active, effective assignment for this academic offering.",
                reason_code="FACULTY_NOT_ASSIGNED",
            )
        return assignment

    @staticmethod
    def create_student(db: Session, data: StudentCreate) -> Student:
        student = Student(**data.model_dump())
        db.add(student)
        db.flush()
        return student

    @staticmethod
    def get_students(db: Session, limit: int = 100) -> List[Student]:
        result = db.execute(select(Student).order_by(Student.roll_number).limit(limit))
        return list(result.scalars().all())

    @staticmethod
    def enroll_student(db: Session, data: EnrollmentCreate) -> Enrollment:
        enrollment = Enrollment(**data.model_dump())
        db.add(enrollment)
        db.flush()
        return enrollment

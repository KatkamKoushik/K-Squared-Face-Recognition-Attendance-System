"""
FRS V7.1 K² — Academic Administration & Eligibility Service.
"""

from datetime import date
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from app.core.errors import PermissionDeniedError, ResourceNotFoundError
from app.domain.enums import EnrollmentStatus, UserRole
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
    def create_cohort(db: Session, data: CohortCreate, user: Optional[User] = None) -> Cohort:
        if user and user.role == UserRole.ADMIN and user.department_id:
            if data.department_id != user.department_id:
                raise PermissionDeniedError(
                    message="Access denied: Department administrator cannot create cohorts in another department.",
                    reason_code="DEPARTMENT_ACCESS_RESTRICTED",
                )
        cohort = Cohort(**data.model_dump())
        db.add(cohort)
        db.flush()
        return cohort

    @staticmethod
    def get_cohorts(db: Session, department_id: Optional[str] = None, user: Optional[User] = None) -> List[Cohort]:
        stmt = select(Cohort).order_by(Cohort.name)
        if user and user.role == UserRole.ADMIN and user.department_id:
            if department_id and department_id != user.department_id:
                raise PermissionDeniedError(
                    message="Access denied: Department administrator cannot access cohorts of another department.",
                    reason_code="DEPARTMENT_ACCESS_RESTRICTED",
                )
            stmt = stmt.where(Cohort.department_id == user.department_id)
        elif department_id:
            stmt = stmt.where(Cohort.department_id == department_id)
        result = db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def create_academic_year(db: Session, data: AcademicYearCreate) -> AcademicYear:
        year = AcademicYear(**data.model_dump())
        db.add(year)
        db.flush()
        return year

    @staticmethod
    def get_academic_years(db: Session) -> List[AcademicYear]:
        result = db.execute(select(AcademicYear).order_by(AcademicYear.year_code.desc()))
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
    def create_subject(db: Session, data: SubjectCreate, user: Optional[User] = None) -> Subject:
        if user and user.role == UserRole.ADMIN and user.department_id:
            if data.department_id != user.department_id:
                raise PermissionDeniedError(
                    message="Access denied: Department administrator cannot create subjects in another department.",
                    reason_code="DEPARTMENT_ACCESS_RESTRICTED",
                )
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
    def get_subjects(db: Session, department_id: Optional[str] = None, user: Optional[User] = None) -> List[Subject]:
        stmt = select(Subject).order_by(Subject.code)
        if user and user.role == UserRole.ADMIN and user.department_id:
            if department_id and department_id != user.department_id:
                raise PermissionDeniedError(
                    message="Access denied: Department administrator cannot access subjects of another department.",
                    reason_code="DEPARTMENT_ACCESS_RESTRICTED",
                )
            stmt = stmt.where(Subject.department_id == user.department_id)
        elif department_id:
            stmt = stmt.where(Subject.department_id == department_id)
        result = db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def create_offering(db: Session, data: SubjectOfferingCreate, user: Optional[User] = None) -> SubjectOffering:
        if user and user.role == UserRole.ADMIN and user.department_id:
            subject = db.get(Subject, data.subject_id)
            if not subject or subject.department_id != user.department_id:
                raise PermissionDeniedError(
                    message="Access denied: Department administrator cannot create offerings for subjects in another department.",
                    reason_code="DEPARTMENT_ACCESS_RESTRICTED",
                )
        offering = SubjectOffering(**data.model_dump())
        db.add(offering)
        db.flush()
        return offering

    @staticmethod
    def get_offerings(db: Session, user: Optional[User] = None) -> List[SubjectOffering]:
        stmt = select(SubjectOffering).order_by(SubjectOffering.id.desc())
        if user and user.role == UserRole.ADMIN and user.department_id:
            stmt = stmt.join(Subject, SubjectOffering.subject_id == Subject.id).where(Subject.department_id == user.department_id)
        result = db.execute(stmt)
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
    def create_student(db: Session, data: StudentCreate, user: Optional[User] = None) -> Student:
        if user and user.role == UserRole.ADMIN and user.department_id:
            cohort = db.get(Cohort, data.cohort_id)
            if not cohort or cohort.department_id != user.department_id:
                raise PermissionDeniedError(
                    message="Access denied: Department administrator cannot register students into another department's cohort.",
                    reason_code="DEPARTMENT_ACCESS_RESTRICTED",
                )
        student = Student(**data.model_dump())
        db.add(student)
        db.flush()
        return student

    @staticmethod
    def get_students(db: Session, limit: int = 100) -> List[Student]:
        result = db.execute(select(Student).order_by(Student.roll_number).limit(limit))
        return list(result.scalars().all())

    @staticmethod
    def get_students_scoped(
        db: Session,
        user: Optional[User] = None,
        cohort_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Student]:
        """
        Retrieves students adhering to strict object-level authorization scopes:
        - DEVELOPER / SUPER_ADMIN: Campus-wide institutional scope across all cohorts and departments.
        - ADMIN: Department-scoped strictly to cohorts in the administrator's assigned department.
        - FACULTY / SUB_ADMIN: Scoped strictly to cohorts and enrollments in subjects actively assigned to the instructor.
        - STUDENT: Self-scoped strictly to the logged-in student's identity.
        """
        if user is None or user.role in (UserRole.DEVELOPER, UserRole.SUPER_ADMIN):
            stmt = select(Student)
            if cohort_id:
                stmt = stmt.where(Student.cohort_id == cohort_id)
            result = db.execute(stmt.order_by(Student.roll_number).limit(limit))
            return list(result.scalars().all())

        if user.role == UserRole.ADMIN:
            stmt = select(Student).join(Cohort, Student.cohort_id == Cohort.id)
            if user.department_id:
                if cohort_id:
                    cohort = db.get(Cohort, cohort_id)
                    if not cohort or cohort.department_id != user.department_id:
                        raise PermissionDeniedError(
                            message="Access denied: Department administrator cannot access students in another department's cohort.",
                            reason_code="DEPARTMENT_ACCESS_RESTRICTED",
                        )
                    stmt = stmt.where(Student.cohort_id == cohort_id)
                else:
                    stmt = stmt.where(Cohort.department_id == user.department_id)
            elif cohort_id:
                stmt = stmt.where(Student.cohort_id == cohort_id)
            result = db.execute(stmt.order_by(Student.roll_number).limit(limit))
            return list(result.scalars().all())

        if user.role == UserRole.STUDENT:
            stmt = select(Student).where(Student.institutional_email == user.email)
            result = db.execute(stmt.limit(1))
            return list(result.scalars().all())

        if user.role in (UserRole.FACULTY, UserRole.SUB_ADMIN):
            faculty = db.execute(select(Faculty).where(Faculty.user_id == user.id)).scalar_one_or_none()
            if not faculty:
                raise PermissionDeniedError(
                    message="Authenticated user does not possess an active faculty profile.",
                    reason_code="FACULTY_PROFILE_NOT_FOUND",
                )

            # Active faculty assignments
            today = date.today()
            assignments = list(
                db.execute(
                    select(FacultyAssignment).where(
                        and_(
                            FacultyAssignment.faculty_id == faculty.id,
                            FacultyAssignment.is_active == True,
                            FacultyAssignment.start_date <= today,
                            FacultyAssignment.end_date >= today,
                        )
                    )
                ).scalars().all()
            )
            assigned_offering_ids = [a.offering_id for a in assignments]
            if not assigned_offering_ids:
                return []

            # Cohorts associated with these offerings via authorized class groups
            assigned_cohort_ids = list(
                db.execute(
                    select(ClassGroupMemberCohort.cohort_id)
                    .join(AuthorizedClassGroup, ClassGroupMemberCohort.group_id == AuthorizedClassGroup.id)
                    .where(AuthorizedClassGroup.offering_id.in_(assigned_offering_ids))
                ).scalars().all()
            )

            # Students directly enrolled in these offerings
            enrolled_student_ids = list(
                db.execute(
                    select(Enrollment.student_id).where(
                        and_(
                            Enrollment.offering_id.in_(assigned_offering_ids),
                            Enrollment.status == EnrollmentStatus.ACTIVE,
                        )
                    )
                ).scalars().all()
            )

            # If a specific cohort_id is requested, verify faculty is assigned to it
            if cohort_id:
                if cohort_id not in assigned_cohort_ids:
                    # Check if any directly enrolled students belong to this cohort
                    cohort_enrolled = db.execute(
                        select(Student.id).where(
                            and_(
                                Student.cohort_id == cohort_id,
                                Student.id.in_(enrolled_student_ids),
                            )
                        ).limit(1)
                    ).scalar_one_or_none()
                    if not cohort_enrolled:
                        raise PermissionDeniedError(
                            message="Instructor is not authorized to access students in this cohort.",
                            reason_code="COHORT_NOT_ASSIGNED",
                        )
                stmt = select(Student).where(
                    and_(
                        Student.cohort_id == cohort_id,
                        (Student.cohort_id.in_(assigned_cohort_ids) | Student.id.in_(enrolled_student_ids)),
                    )
                )
            else:
                stmt = select(Student).where(
                    (Student.cohort_id.in_(assigned_cohort_ids) | Student.id.in_(enrolled_student_ids))
                )

            result = db.execute(stmt.order_by(Student.roll_number).limit(limit))
            return list(result.scalars().all())

        raise PermissionDeniedError(
            message="Role not authorized to access student directory.",
            reason_code="ROLE_NOT_AUTHORIZED",
        )

    @staticmethod
    def enroll_student(db: Session, data: EnrollmentCreate) -> Enrollment:
        enrollment = Enrollment(**data.model_dump())
        db.add(enrollment)
        db.flush()
        return enrollment

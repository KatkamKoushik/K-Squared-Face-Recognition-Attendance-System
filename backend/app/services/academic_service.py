"""
FRS V7.1 K² — Academic Administration & Eligibility Service.
"""

from datetime import date, datetime, timezone
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from app.core.errors import PermissionDeniedError, ResourceNotFoundError
from app.domain.enums import EnrollmentStatus, UserRole, StudentLifecycleStatus, AuditAction
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
from app.domain.models.audit import AuditEvent
from app.schemas.academic import (
    DepartmentCreate,
    DepartmentUpdate,
    CohortCreate,
    CohortUpdate,
    AcademicYearCreate,
    AcademicYearUpdate,
    TermCreate,
    TermUpdate,
    SubjectCreate,
    SubjectUpdate,
    SubjectOfferingCreate,
    SubjectOfferingUpdate,
    AuthorizedClassGroupCreate,
    FacultyAssignmentCreate,
    StudentCreate,
    StudentLifecycleUpdate,
    CohortRolloverRequest,
    CohortRolloverResponse,
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
        if user and user.role == UserRole.ADMIN:
            if not user.department_id:
                raise PermissionDeniedError(
                    message="Access denied: Department administrator has no assigned department.",
                    reason_code="DEPARTMENT_ACCESS_RESTRICTED",
                )
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
        if user and user.role == UserRole.ADMIN:
            if not user.department_id:
                raise PermissionDeniedError(
                    message="Access denied: Department administrator has no assigned department.",
                    reason_code="DEPARTMENT_ACCESS_RESTRICTED",
                )
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
        if user and user.role == UserRole.ADMIN:
            if not user.department_id:
                raise PermissionDeniedError(
                    message="Access denied: Department administrator has no assigned department.",
                    reason_code="DEPARTMENT_ACCESS_RESTRICTED",
                )
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
        if user and user.role == UserRole.ADMIN:
            if not user.department_id:
                raise PermissionDeniedError(
                    message="Access denied: Department administrator has no assigned department.",
                    reason_code="DEPARTMENT_ACCESS_RESTRICTED",
                )
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
        if user and user.role == UserRole.ADMIN:
            if not user.department_id:
                raise PermissionDeniedError(
                    message="Access denied: Department administrator has no assigned department.",
                    reason_code="DEPARTMENT_ACCESS_RESTRICTED",
                )
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
        if user and user.role == UserRole.ADMIN:
            if not user.department_id:
                raise PermissionDeniedError(
                    message="Access denied: Department administrator has no assigned department.",
                    reason_code="DEPARTMENT_ACCESS_RESTRICTED",
                )
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
        if user and user.role == UserRole.ADMIN:
            if not user.department_id:
                raise PermissionDeniedError(
                    message="Access denied: Department administrator has no assigned department.",
                    reason_code="DEPARTMENT_ACCESS_RESTRICTED",
                )
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
            if not user.department_id:
                raise PermissionDeniedError(
                    message="Access denied: Department administrator has no assigned department.",
                    reason_code="DEPARTMENT_ACCESS_RESTRICTED",
                )
            stmt = select(Student).join(Cohort, Student.cohort_id == Cohort.id)
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

    @staticmethod
    def update_department(db: Session, dept_id: str, data: DepartmentUpdate) -> Department:
        dept = db.get(Department, dept_id)
        if not dept:
            raise ResourceNotFoundError(resource="Department", identifier=dept_id)
        if data.name is not None:
            dept.name = data.name
        if data.is_active is not None:
            dept.is_active = data.is_active
        db.flush()
        return dept

    @staticmethod
    def update_cohort(db: Session, cohort_id: str, data: CohortUpdate, user: Optional[User] = None) -> Cohort:
        cohort = db.get(Cohort, cohort_id)
        if not cohort:
            raise ResourceNotFoundError(resource="Cohort", identifier=cohort_id)
        if user and user.role == UserRole.ADMIN:
            if not user.department_id or cohort.department_id != user.department_id:
                raise PermissionDeniedError(
                    message="Access denied: Department administrator cannot update cohorts in another department.",
                    reason_code="DEPARTMENT_ACCESS_RESTRICTED",
                )
        if data.name is not None:
            cohort.name = data.name
        if data.admission_year is not None:
            cohort.admission_year = data.admission_year
        if data.graduation_year is not None:
            cohort.graduation_year = data.graduation_year
        if data.is_active is not None:
            cohort.is_active = data.is_active
        db.flush()
        return cohort

    @staticmethod
    def update_academic_year(db: Session, year_id: str, data: AcademicYearUpdate) -> AcademicYear:
        ay = db.get(AcademicYear, year_id)
        if not ay:
            raise ResourceNotFoundError(resource="AcademicYear", identifier=year_id)
        if data.year_code is not None:
            ay.year_code = data.year_code
        if data.start_date is not None:
            ay.start_date = data.start_date
        if data.end_date is not None:
            ay.end_date = data.end_date
        if data.is_current is not None:
            ay.is_current = data.is_current
        db.flush()
        return ay

    @staticmethod
    def update_term(db: Session, term_id: str, data: TermUpdate) -> Term:
        term = db.get(Term, term_id)
        if not term:
            raise ResourceNotFoundError(resource="Term", identifier=term_id)
        if data.term_type is not None:
            term.term_type = data.term_type
        if data.start_date is not None:
            term.start_date = data.start_date
        if data.end_date is not None:
            term.end_date = data.end_date
        if data.is_active is not None:
            term.is_active = data.is_active
        db.flush()
        return term

    @staticmethod
    def update_subject(db: Session, subject_id: str, data: SubjectUpdate, user: Optional[User] = None) -> Subject:
        subject = db.get(Subject, subject_id)
        if not subject:
            raise ResourceNotFoundError(resource="Subject", identifier=subject_id)
        if user and user.role == UserRole.ADMIN:
            if not user.department_id or subject.department_id != user.department_id:
                raise PermissionDeniedError(
                    message="Access denied: Department administrator cannot update subjects in another department.",
                    reason_code="DEPARTMENT_ACCESS_RESTRICTED",
                )
        if data.code is not None:
            subject.code = data.code.upper()
        if data.name is not None:
            subject.name = data.name
        if data.credits is not None:
            subject.credits = data.credits
        db.flush()
        return subject

    @staticmethod
    def update_offering(db: Session, offering_id: str, data: SubjectOfferingUpdate, user: Optional[User] = None) -> SubjectOffering:
        offering = db.get(SubjectOffering, offering_id)
        if not offering:
            raise ResourceNotFoundError(resource="SubjectOffering", identifier=offering_id)
        if user and user.role == UserRole.ADMIN:
            subject = db.get(Subject, offering.subject_id)
            if not subject or not user.department_id or subject.department_id != user.department_id:
                raise PermissionDeniedError(
                    message="Access denied: Department administrator cannot update offerings in another department.",
                    reason_code="DEPARTMENT_ACCESS_RESTRICTED",
                )
        if data.section is not None:
            offering.section = data.section
        if data.is_active is not None:
            offering.is_active = data.is_active
        db.flush()
        return offering

    @staticmethod
    def update_student_lifecycle(
        db: Session,
        student_id: str,
        status: StudentLifecycleStatus,
        reason: str,
        user: User,
        correlation_id: str,
    ) -> Student:
        student = db.get(Student, student_id)
        if not student:
            raise ResourceNotFoundError(resource="Student", identifier=student_id)
        cohort = db.get(Cohort, student.cohort_id)
        if user.role == UserRole.ADMIN:
            if not user.department_id or not cohort or cohort.department_id != user.department_id:
                raise PermissionDeniedError(
                    message="Access denied: Department administrator cannot update student lifecycle in another department.",
                    reason_code="DEPARTMENT_ACCESS_RESTRICTED",
                )
        prev_status = student.lifecycle_status.value if hasattr(student.lifecycle_status, "value") else str(student.lifecycle_status)
        new_status = status.value if hasattr(status, "value") else str(status)

        student.lifecycle_status = status
        student.is_active = (status == StudentLifecycleStatus.ACTIVE)

        audit = AuditEvent(
            session_id=None,
            actor_id=user.id,
            action=AuditAction.STUDENT_LIFECYCLE_UPDATED,
            reason=reason,
            before_state={"student_id": student.id, "roll_number": student.roll_number, "lifecycle_status": prev_status},
            after_state={"student_id": student.id, "roll_number": student.roll_number, "lifecycle_status": new_status},
            correlation_id=correlation_id,
        )
        db.add(audit)
        db.flush()
        return student

    @staticmethod
    def rollover_cohort(
        db: Session,
        from_cohort_id: str,
        to_cohort_id: str,
        reason: str,
        user: User,
        correlation_id: str,
    ) -> dict:
        from_cohort = db.get(Cohort, from_cohort_id)
        if not from_cohort:
            raise ResourceNotFoundError(resource="Cohort", identifier=from_cohort_id)
        to_cohort = db.get(Cohort, to_cohort_id)
        if not to_cohort:
            raise ResourceNotFoundError(resource="Cohort", identifier=to_cohort_id)

        if user.role == UserRole.ADMIN:
            if (
                not user.department_id
                or from_cohort.department_id != user.department_id
                or to_cohort.department_id != user.department_id
            ):
                raise PermissionDeniedError(
                    message="Access denied: Department administrator cannot perform rollover across department boundaries.",
                    reason_code="DEPARTMENT_ACCESS_RESTRICTED",
                )

        students_stmt = select(Student).where(
            and_(
                Student.cohort_id == from_cohort_id,
                Student.lifecycle_status == StudentLifecycleStatus.ACTIVE,
            )
        )
        students = list(db.execute(students_stmt).scalars().all())

        for s in students:
            s.cohort_id = to_cohort_id

        audit = AuditEvent(
            session_id=None,
            actor_id=user.id,
            action=AuditAction.COHORT_ROLLOVER_EXECUTED,
            reason=reason,
            before_state={"from_cohort_id": from_cohort_id, "student_count": len(students)},
            after_state={"to_cohort_id": to_cohort_id, "promoted_count": len(students)},
            correlation_id=correlation_id,
        )
        db.add(audit)
        db.flush()
        return {
            "from_cohort_id": from_cohort_id,
            "to_cohort_id": to_cohort_id,
            "promoted_count": len(students),
            "timestamp": datetime.now(timezone.utc),
        }

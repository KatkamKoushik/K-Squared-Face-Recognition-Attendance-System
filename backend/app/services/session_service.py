"""
FRS V7.1 K² — Session Lifecycle & Conducted Unit Management Service.
"""

from datetime import date
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload, Session
from app.core.errors import ResourceNotFoundError, StateTransitionError
from app.domain.enums import SessionState, UnitStatus
from app.domain.models.session import AttendanceSession, AttendanceUnit, RosterSnapshot
from app.schemas.session import SessionCreateRequest
from app.services.academic_service import AcademicService
from app.services.roster_service import RosterService


class SessionService:

    @staticmethod
    def create_session(
        db: Session,
        faculty_id: str,
        data: SessionCreateRequest,
    ) -> AttendanceSession:
        """
        Initializes an attendance session:
        1. Validates faculty authorization against effective assignment.
        2. Creates session and configured unit structures (1-4).
        3. Freezes immutable roster snapshot.
        """
        session_date = data.session_date or date.today()

        # 1. Server-side faculty assignment check
        AcademicService.verify_faculty_assignment(
            db=db,
            faculty_id=faculty_id,
            offering_id=data.offering_id,
            class_group_id=data.class_group_id,
            check_date=session_date,
        )

        # 2. Create session entity
        session = AttendanceSession(
            offering_id=data.offering_id,
            class_group_id=data.class_group_id,
            faculty_id=faculty_id,
            session_date=session_date,
            state=SessionState.DRAFT,
            planned_units=data.planned_units,
        )
        db.add(session)
        db.flush()

        # 3. Create unit slots (1 to planned_units)
        for i in range(1, data.planned_units + 1):
            unit = AttendanceUnit(
                session_id=session.id,
                unit_index=i,
                is_conducted=True,
                status=UnitStatus.PENDING,
            )
            db.add(unit)
        db.flush()

        # 4. Freeze immutable roster snapshot
        RosterService.freeze_session_roster(
            db=db,
            session_id=session.id,
            offering_id=data.offering_id,
            class_group_id=data.class_group_id,
            effective_date=session_date,
        )

        session.state = SessionState.ROSTER_FROZEN
        db.flush()

        return SessionService.get_session_by_id(db, session.id)

    @staticmethod
    def get_session_by_id(db: Session, session_id: str) -> AttendanceSession:
        stmt = (
            select(AttendanceSession)
            .options(
                selectinload(AttendanceSession.units),
                selectinload(AttendanceSession.snapshot).selectinload(RosterSnapshot.items),
            )
            .where(AttendanceSession.id == session_id)
        )
        session = db.execute(stmt).scalar_one_or_none()
        if not session:
            raise ResourceNotFoundError("AttendanceSession", session_id)
        return session

    @staticmethod
    def confirm_conducted_unit(
        db: Session,
        session_id: str,
        unit_index: int,
        is_conducted: bool,
    ) -> AttendanceUnit:
        """Explicit faculty confirmation of which unit was actually conducted."""
        stmt = select(AttendanceUnit).where(
            and_(
                AttendanceUnit.session_id == session_id,
                AttendanceUnit.unit_index == unit_index,
            )
        )
        unit = db.execute(stmt).scalar_one_or_none()
        if not unit:
            raise ResourceNotFoundError("AttendanceUnit", f"session:{session_id}, unit:{unit_index}")

        unit.is_conducted = is_conducted
        unit.status = UnitStatus.CONDUCTED_CONFIRMED if is_conducted else UnitStatus.NOT_CONDUCTED
        db.flush()
        return unit

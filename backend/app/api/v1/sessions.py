"""
FRS V7.1 K² — Attendance Session & Conducted Unit Endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_faculty, get_optional_current_user, get_correlation_id
from app.core.database import get_db
from app.core.errors import PermissionDeniedError
from app.domain.models.academic import Faculty, User
from app.domain.models.session import AttendanceSession
from app.schemas.common import ResponseEnvelope
from app.schemas.session import (
    SessionCreateRequest,
    SessionResponse,
    UnitResponse,
    UnitConfirmationRequest,
    RosterSnapshotResponse,
    SnapshotStudentResponse,
)
from app.services.session_service import SessionService
from app.services.roster_service import RosterService

router = APIRouter(prefix="/sessions", tags=["Attendance Sessions"])


@router.post("", response_model=ResponseEnvelope[SessionResponse], status_code=status.HTTP_201_CREATED)
def create_session(
    data: SessionCreateRequest,
    db: Session = Depends(get_db),
    faculty: Faculty = Depends(get_current_faculty),
    correlation_id: str = Depends(get_correlation_id),
):
    """
    Initializes a new attendance session:
    Verifies faculty assignment, builds unit slots, freezes immutable roster snapshot.
    """
    session = SessionService.create_session(db, faculty.id, data)
    return ResponseEnvelope(data=SessionResponse.model_validate(session), correlation_id=correlation_id)


@router.get("", response_model=ResponseEnvelope[List[SessionResponse]])
def list_recent_sessions(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
    correlation_id: str = Depends(get_correlation_id),
):
    """Returns recent attendance sessions from the authoritative ledger."""
    stmt = select(AttendanceSession).order_by(AttendanceSession.created_at.desc()).limit(limit)
    sessions = list(db.execute(stmt).scalars().all())
    items = [SessionResponse.model_validate(s) for s in sessions]
    return ResponseEnvelope(data=items, correlation_id=correlation_id)


@router.get("/{session_id}", response_model=ResponseEnvelope[SessionResponse])
def get_session(
    session_id: str,
    db: Session = Depends(get_db),
    faculty: Faculty = Depends(get_current_faculty),
    correlation_id: str = Depends(get_correlation_id),
):
    session = SessionService.get_session_by_id(db, session_id)
    if session.faculty_id != faculty.id:
        raise PermissionDeniedError(
            message="You are not authorized to view this session.",
            reason_code="FACULTY_MISMATCH",
        )
    return ResponseEnvelope(data=SessionResponse.model_validate(session), correlation_id=correlation_id)


@router.get("/{session_id}/roster", response_model=ResponseEnvelope[RosterSnapshotResponse])
def get_session_roster(
    session_id: str,
    db: Session = Depends(get_db),
    faculty: Faculty = Depends(get_current_faculty),
    correlation_id: str = Depends(get_correlation_id),
):
    """Returns the immutable frozen roster snapshot for the session."""
    session = SessionService.get_session_by_id(db, session_id)
    if session.faculty_id != faculty.id:
        raise PermissionDeniedError(
            message="You are not authorized to view this session roster.",
            reason_code="FACULTY_MISMATCH",
        )
    snapshot = session.snapshot
    students = [
        SnapshotStudentResponse(
            student_id=item.student_id,
            roll_number=item.roll_number,
            full_name=item.full_name,
            cohort_id=item.cohort_id,
        )
        for item in snapshot.items
    ]
    res = RosterSnapshotResponse(
        id=snapshot.id,
        session_id=snapshot.session_id,
        snapshot_version=snapshot.snapshot_version,
        total_eligible_students=snapshot.total_eligible_students,
        frozen_at=snapshot.frozen_at,
        students=students,
    )
    return ResponseEnvelope(data=res, correlation_id=correlation_id)


@router.post("/{session_id}/units/{unit_index}/confirm", response_model=ResponseEnvelope[UnitResponse])
def confirm_unit(
    session_id: str,
    unit_index: int,
    data: UnitConfirmationRequest,
    db: Session = Depends(get_db),
    faculty: Faculty = Depends(get_current_faculty),
    correlation_id: str = Depends(get_correlation_id),
):
    """Explicitly confirms whether instructional unit was conducted."""
    session = SessionService.get_session_by_id(db, session_id)
    if session.faculty_id != faculty.id:
        raise PermissionDeniedError(
            message="You are not authorized to modify instructional units for this session.",
            reason_code="FACULTY_MISMATCH",
        )
    unit = SessionService.confirm_conducted_unit(
        db=db,
        session_id=session_id,
        unit_index=unit_index,
        is_conducted=data.is_conducted,
    )
    return ResponseEnvelope(data=UnitResponse.model_validate(unit), correlation_id=correlation_id)

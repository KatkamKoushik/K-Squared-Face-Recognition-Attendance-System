"""
FRS V7.1 K² — Data Governance, Biometric Privacy & Retention Endpoints.
Provides institutional compliance telemetry, raw frame purging, and consent controls.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user, get_correlation_id
from app.core.database import get_db
from app.domain.models.academic import User
from app.schemas.common import ResponseEnvelope
from app.schemas.governance import (
    PurgeRequest,
    PurgeResponse,
    StudentConsentStatus,
    ConsentToggleRequest,
    GovernanceSummaryResponse,
)
from app.services.governance_service import GovernanceService

router = APIRouter(prefix="/governance", tags=["Data Governance & Privacy"])


@router.get("/status", response_model=ResponseEnvelope[GovernanceSummaryResponse])
def get_governance_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id),
):
    """
    Retrieves institutional biometric compliance metrics, raw frame disk usage,
    and data retention purge telemetry.
    """
    summary = GovernanceService.get_governance_summary(db)
    return ResponseEnvelope(data=summary, correlation_id=correlation_id)


@router.post(
    "/purge",
    response_model=ResponseEnvelope[PurgeResponse],
    status_code=status.HTTP_200_OK,
)
def purge_raw_frames(
    request: PurgeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id),
):
    """
    Executes raw frame physical purging for finalized attendance sessions per retention policy.
    Restricted to system administrators. Emits an immutable DATA_PURGE_EXECUTED audit event.
    """
    result = GovernanceService.purge_raw_frames(
        db=db,
        request=request,
        user=current_user,
        correlation_id=correlation_id,
    )
    return ResponseEnvelope(data=result, correlation_id=correlation_id)


@router.post(
    "/consent",
    response_model=ResponseEnvelope[StudentConsentStatus],
    status_code=status.HTTP_200_OK,
)
def toggle_student_consent(
    request: ConsentToggleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id),
):
    """
    Updates student biometric consent status. When deactivated, the student's
    biometric profile is disabled and routed to non-biometric manual roll-call.
    """
    result = GovernanceService.toggle_student_biometric_consent(
        db=db,
        request=request,
        user=current_user,
        correlation_id=correlation_id,
    )
    return ResponseEnvelope(data=result, correlation_id=correlation_id)


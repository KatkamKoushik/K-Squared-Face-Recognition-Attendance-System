"""
K² FRS — Audit Trail Schemas.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.domain.enums import AuditAction


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: Optional[str]
    actor_id: str
    action: AuditAction
    reason: str
    before_state: Optional[Dict[str, Any]]
    after_state: Optional[Dict[str, Any]]
    correlation_id: str
    timestamp: datetime

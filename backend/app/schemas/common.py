"""
K² FRS — Common Schema Envelopes & Pagination Contracts.
"""

from datetime import datetime, timezone
from typing import Generic, Optional, TypeVar, List, Dict, Any
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ResponseEnvelope(BaseModel, Generic[DataT]):
    """Standard success response wrapper."""
    success: bool = True
    data: DataT
    correlation_id: str = Field(default="system", description="Unique trace correlation ID")
    timestamp: datetime = Field(default_factory=utc_now)


class ErrorDetail(BaseModel):
    code: str
    message: str
    reason_code: str
    details: Optional[Dict[str, Any]] = None


class ErrorEnvelope(BaseModel):
    """Standard error response wrapper."""
    success: bool = False
    error: ErrorDetail
    correlation_id: str
    timestamp: datetime = Field(default_factory=utc_now)


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)


class PaginatedResponse(BaseModel, Generic[DataT]):
    items: List[DataT]
    total: int
    page: int
    page_size: int
    total_pages: int

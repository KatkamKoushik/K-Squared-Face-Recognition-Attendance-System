"""
FRS V7.1 K² — Error Taxonomy & Custom Exceptions.
Provides uniform reason codes and deterministic HTTP exception mappings.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class AppBaseException(HTTPException):
    """Base application exception mapping directly to our error envelope."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        reason_code: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.reason_code = reason_code
        self.details = details or {}


class AuthenticationError(AppBaseException):
    def __init__(self, message: str = "Authentication required or credentials invalid", reason_code: str = "AUTH_INVALID"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="AUTHENTICATION_FAILED",
            message=message,
            reason_code=reason_code,
        )


class PermissionDeniedError(AppBaseException):
    def __init__(self, message: str = "Actor lacks authorized access to requested academic resource", reason_code: str = "ACCESS_FORBIDDEN"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="RESOURCE_FORBIDDEN",
            message=message,
            reason_code=reason_code,
        )


class ResourceNotFoundError(AppBaseException):
    def __init__(self, resource: str, identifier: Any, reason_code: str = "RESOURCE_NOT_FOUND"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=f"Requested {resource} with ID '{identifier}' does not exist.",
            reason_code=reason_code,
        )


class StateTransitionError(AppBaseException):
    def __init__(self, message: str, current_state: str, attempted_state: str, reason_code: str = "ILLEGAL_STATE_TRANSITION"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="STATE_CONFLICT",
            message=message,
            reason_code=reason_code,
            details={"current_state": current_state, "attempted_state": attempted_state},
        )


class IdempotencyConflictError(AppBaseException):
    def __init__(self, key: str, message: str = "A request with this idempotency key has already committed with different payload"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="IDEMPOTENCY_CONFLICT",
            message=message,
            reason_code="IDEMPOTENCY_MISMATCH",
            details={"idempotency_key": key},
        )


class ConflictError(AppBaseException):
    def __init__(self, resource: str, identifier: Any, message: Optional[str] = None, reason_code: str = "RESOURCE_CONFLICT"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="RESOURCE_CONFLICT",
            message=message or f"Conflict on {resource} with ID '{identifier}'.",
            reason_code=reason_code,
            details={"resource": resource, "identifier": str(identifier)},
        )


class IngressValidationError(AppBaseException):
    def __init__(self, message: str, reason_code: str = "INVALID_IMAGE_PAYLOAD", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="INGRESS_VALIDATION_FAILED",
            message=message,
            reason_code=reason_code,
            details=details,
        )


class PipelineExecutionError(AppBaseException):
    def __init__(self, message: str, reason_code: str = "PIPELINE_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="PIPELINE_ERROR",
            message=message,
            reason_code=reason_code,
            details=details,
        )


class BusinessRuleViolationError(AppBaseException):
    def __init__(self, message: str, reason_code: str = "BUSINESS_RULE_VIOLATION", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="UNPROCESSABLE_ENTITY",
            message=message,
            reason_code=reason_code,
            details=details,
        )


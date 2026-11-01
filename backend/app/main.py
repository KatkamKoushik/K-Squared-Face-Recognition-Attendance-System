"""
FRS V7.1 K² — FastAPI Control Plane Application Factory & Lifecycle.
"""

from contextlib import asynccontextmanager
import logging
import uuid
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.api.v1.api_router import api_router
from app.core.config import settings
from app.core.database import engine, Base
from app.core.errors import AppBaseException
from app.core.logging import setup_logging
from app.core.rate_limiter import rate_limiting_middleware
from app.schemas.common import ErrorEnvelope, ErrorDetail

logger = logging.getLogger("app.lifecycle")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    setup_logging()
    if settings.ENVIRONMENT in ["production", "staging"]:
        # In production and staging, schema evolution is governed by Alembic migrations.
        # Fail-fast immediately if database is unreachable; never mask persistence failures.
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as exc:
            logger.critical(f"FATAL: Database connectivity check failed during startup: {exc}")
            raise RuntimeError(f"Database unavailable during {settings.ENVIRONMENT} startup") from exc
    elif settings.ENVIRONMENT != "test":
        try:
            Base.metadata.create_all(bind=engine)
        except Exception as exc:
            logger.warning(f"Development schema sync notice: {exc}")
    yield
    if settings.ENVIRONMENT != "test":
        try:
            engine.dispose()
        except Exception:
            pass


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="7.1.0",
        description="Authoritative API Control Plane for KUCET Classroom Attendance Proposal System.",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # 1. CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Security Headers Middleware (Checklist Section 11)
    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(self), microphone=(), geolocation=()"
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    # 3. Rate Limiting Middleware (Checklist Section 6 & 11)
    app.middleware("http")(rate_limiting_middleware)

    # 4. Ingress Payload Size & Media Type Guardrail Middleware (Checklist Controls 28-N006 & 28-B031)
    @app.middleware("http")
    async def payload_guardrail_middleware(request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            # A. Enforce Content-Length before expensive parsing or buffering
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    length = int(content_length)
                    max_allowed = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
                    if length > max_allowed:
                        corr_id = request.headers.get("X-Correlation-ID") or getattr(
                            request.state, "correlation_id", "size-limit"
                        )
                        envelope = ErrorEnvelope(
                            error=ErrorDetail(
                                code="PAYLOAD_TOO_LARGE",
                                message=f"Payload size of {length} bytes exceeds the maximum allowed limit of {max_allowed} bytes ({settings.MAX_UPLOAD_SIZE_MB} MB).",
                                reason_code="CONTENT_LENGTH_EXCEEDED",
                                details={"max_bytes": max_allowed, "received_bytes": length},
                            ),
                            correlation_id=corr_id,
                        )
                        return JSONResponse(
                            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                            content=envelope.model_dump(mode="json"),
                        )
                except ValueError:
                    pass

            # B. Enforce Content-Type verification (reject prohibited or executable media types)
            content_type = request.headers.get("content-type")
            if content_type:
                ct_clean = content_type.split(";")[0].strip().lower()
                prohibited_media_types = {
                    "application/x-msdownload",
                    "application/x-sh",
                    "application/x-dosexec",
                }
                if ct_clean in prohibited_media_types:
                    corr_id = request.headers.get("X-Correlation-ID") or getattr(
                        request.state, "correlation_id", "media-type"
                    )
                    envelope = ErrorEnvelope(
                        error=ErrorDetail(
                            code="UNSUPPORTED_MEDIA_TYPE",
                            message=f"Media type '{ct_clean}' is not supported or prohibited by policy.",
                            reason_code="PROHIBITED_MEDIA_TYPE",
                            details={"content_type": ct_clean},
                        ),
                        correlation_id=corr_id,
                    )
                    return JSONResponse(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        content=envelope.model_dump(mode="json"),
                    )

        return await call_next(request)

    # 4. Correlation ID Middleware (Checklist Section 7 & 33)
    @app.middleware("http")
    async def correlation_id_middleware(request: Request, call_next):
        corr_id = request.headers.get("X-Correlation-ID") or f"req-{uuid.uuid4().hex[:12]}"
        request.state.correlation_id = corr_id
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = corr_id
        return response

    # 5. Custom Exception Handlers
    @app.exception_handler(AppBaseException)
    async def app_exception_handler(request: Request, exc: AppBaseException):
        corr_id = getattr(request.state, "correlation_id", "none")
        envelope = ErrorEnvelope(
            error=ErrorDetail(
                code=exc.code,
                message=exc.message,
                reason_code=exc.reason_code,
                details=exc.details,
            ),
            correlation_id=corr_id,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=envelope.model_dump(mode="json"),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        corr_id = getattr(request.state, "correlation_id", "none")
        envelope = ErrorEnvelope(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="Request body or query parameters failed schema validation.",
                reason_code="SCHEMA_VALIDATION_FAILED",
                details={"errors": exc.errors()},
            ),
            correlation_id=corr_id,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=envelope.model_dump(mode="json"),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        corr_id = getattr(request.state, "correlation_id", "none")
        envelope = ErrorEnvelope(
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected internal server error occurred.",
                reason_code="UNHANDLED_EXCEPTION",
                details={"error_type": type(exc).__name__} if settings.DEBUG else None,
            ),
            correlation_id=corr_id,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=envelope.model_dump(mode="json"),
        )

    # 4. Mount API v1 router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_application()

"""
K² FRS — Central API v1 Router.
"""

from fastapi import APIRouter
from app.api.v1 import health, auth, academic, sessions, capture, review, attendance, audit, governance, enrollment, student, demo, events
from app.core.config import settings

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(academic.router)
api_router.include_router(sessions.router)
api_router.include_router(capture.router)
api_router.include_router(review.router)
api_router.include_router(attendance.router)
api_router.include_router(audit.router)
api_router.include_router(governance.router)
api_router.include_router(enrollment.router)
api_router.include_router(student.router)

# R09: Gate demo router in production release mode (unmounted / 404 in production)
if settings.ENVIRONMENT != "production" and getattr(settings, "DEMO_ENABLED", True):
    api_router.include_router(demo.router)

api_router.include_router(events.router)

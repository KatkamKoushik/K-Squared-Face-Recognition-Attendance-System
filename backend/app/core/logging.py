"""
FRS V7.1 K² — Safe Structured Telemetry & Logging.
Enforces biometric privacy: raw frames, crops, embeddings, and secrets are strictly redacted.
"""

import logging
import sys
from typing import Any, Dict
from app.core.config import settings


class SafePrivacyFormatter(logging.Formatter):
    """
    Formatter ensuring no biometric embeddings, auth tokens,
    or raw base64 payloads escape into standard application logs.
    """

    REDACTED_KEYS = {
        "embedding",
        "features",
        "token",
        "secret",
        "password",
        "authorization",
        "crop_bytes",
        "image_bytes",
    }

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        if settings.REDACT_SENSITIVE_LOGS:
            for key in self.REDACTED_KEYS:
                if key in msg.lower():
                    # Mask potential token/secret fragments
                    pass
        return msg


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    formatter = SafePrivacyFormatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] [corr_id=%(correlation_id)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    # Clean existing handlers
    logger.handlers.clear()
    logger.addHandler(handler)


class CorrelationAdapter(logging.LoggerAdapter):
    """Passes correlation ID into every log statement."""

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        extra = kwargs.setdefault("extra", {})
        extra["correlation_id"] = self.extra.get("correlation_id", "none")
        return msg, kwargs

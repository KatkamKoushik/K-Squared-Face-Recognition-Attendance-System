"""
FRS V7.1 K² — Safe Structured Telemetry & Logging.
Enforces biometric privacy: raw frames, crops, embeddings, and secrets are strictly redacted.
"""

from datetime import datetime, timezone
import json
import logging
import re
import sys
from typing import Any, Dict
from app.core.config import settings


class SafePrivacyFormatter(logging.Formatter):
    """
    Formatter ensuring no biometric embeddings, auth tokens,
    passwords, or raw image payloads escape into standard application logs.
    """

    REDACTION_PATTERNS = [
        # Bearer tokens
        (re.compile(r'(?i)bearer\s+[a-zA-Z0-9_\-\.]+', re.IGNORECASE), "Bearer [REDACTED_TOKEN]"),
        # Key / Secret / Password fields in key=value or "key": "value"
        (re.compile(r'(?i)(password|secret_key|secret|hashed_password|access_token|refresh_token)\s*([:=])\s*["\']?[^"\'\s,{}]+["\']?', re.IGNORECASE), r'\1\2"[REDACTED]"'),
        # Large floating-point arrays (biometric embedding vectors >= 5 floats)
        (re.compile(r'\[(?:\s*-?\d+\.\d+\s*,?){5,}\]'), "[REDACTED_EMBEDDING_VECTOR]"),
        # Base64 image payloads
        (re.compile(r'data:image\/[a-zA-Z]+;base64,[a-zA-Z0-9+/=]{30,}'), "[REDACTED_IMAGE_BYTES]"),
    ]

    def redact(self, text: str) -> str:
        if not getattr(settings, "REDACT_SENSITIVE_LOGS", True):
            return text
        redacted = text
        for pattern, replacement in self.REDACTION_PATTERNS:
            redacted = pattern.sub(replacement, redacted)
        return redacted

    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        redacted = self.redact(formatted)

        if getattr(settings, "LOG_FORMAT", "text").lower() == "json":
            corr_id = getattr(record, "correlation_id", "none")
            log_dict = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname,
                "name": record.name,
                "correlation_id": corr_id,
                "message": self.redact(record.getMessage()),
            }
            if record.exc_text:
                log_dict["exception"] = self.redact(record.exc_text)
            return json.dumps(log_dict)

        return redacted


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

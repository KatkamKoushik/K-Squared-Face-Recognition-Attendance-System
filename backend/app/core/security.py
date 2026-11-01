"""
FRS V7.1 K² — Cryptographic Security, Password Hashing & JWT Management.
Uses NIST-approved PBKDF2-HMAC-SHA256 (standard library) and PyJWT for fail-safe operation.
"""

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
from typing import Any, Dict, Optional
import jwt
from app.core.config import settings
from app.core.errors import AuthenticationError


def hash_password(password: str) -> str:
    """Hashes password using PBKDF2-HMAC-SHA256 with 100,000 iterations and salt."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}:{key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored salt:hash string."""
    try:
        salt_hex, key_hex = hashed_password.split(":")
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        computed_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100_000)
        return hmac.compare_digest(computed_key, expected_key)
    except Exception:
        return False


def create_access_token(
    subject: str,
    role: str,
    additional_claims: Optional[Dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Creates a signed, scoped JWT access token."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": subject,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "iss": settings.APP_NAME,
    }
    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT token; fails closed if expired or altered."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            issuer=settings.APP_NAME,
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Access token has expired", reason_code="TOKEN_EXPIRED")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid access token signature", reason_code="TOKEN_INVALID")

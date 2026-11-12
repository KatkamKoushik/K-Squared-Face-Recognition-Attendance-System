"""
K² FRS — Cryptographic Security, Password Hashing & JWT Management.
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


def init_firebase_admin() -> bool:
    """Initializes Firebase Admin SDK if not already initialized."""
    try:
        import firebase_admin
        from firebase_admin import credentials

        if firebase_admin._apps:
            return True

        cred_path = settings.FIREBASE_CREDENTIALS_PATH or os.environ.get("FIREBASE_CREDENTIALS_PATH")
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {"projectId": settings.FIREBASE_PROJECT_ID})
            return True
        elif os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            firebase_admin.initialize_app()
            return True
        elif settings.FIREBASE_PROJECT_ID:
            firebase_admin.initialize_app(options={"projectId": settings.FIREBASE_PROJECT_ID})
            return True
    except Exception:
        pass
    return False


def verify_firebase_id_token(token: str) -> Dict[str, Any]:
    """
    Verifies a Firebase ID token.
    Returns decoded token dictionary with user identifier and email.
    """
    try:
        from firebase_admin import auth as fb_auth

        init_firebase_admin()
        decoded = fb_auth.verify_id_token(token)
        return {
            "sub": decoded.get("uid"),
            "user_id": decoded.get("uid"),
            "email": decoded.get("email"),
            "email_verified": decoded.get("email_verified", False),
            "role": decoded.get("role"),
            "token_type": "firebase_id_token",
            "firebase": decoded,
        }
    except Exception as e:
        raise AuthenticationError(f"Firebase token verification failed: {str(e)}", reason_code="FIREBASE_TOKEN_INVALID")


def verify_token(token: str) -> Dict[str, Any]:
    """
    Unified token validator supporting both internal HMAC JWTs and Firebase ID tokens.
    Tries internal JWT decoding first; falls back to Firebase ID token verification.
    """
    # 1. Try decoding as local signed JWT
    try:
        return decode_access_token(token)
    except AuthenticationError as e:
        if e.reason_code == "TOKEN_EXPIRED":
            raise

    # 2. Try Firebase ID token verification
    try:
        return verify_firebase_id_token(token)
    except Exception:
        pass

    raise AuthenticationError("Invalid or expired authentication credentials", reason_code="TOKEN_INVALID")

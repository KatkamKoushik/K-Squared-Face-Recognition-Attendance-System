"""
FRS V7.1 K² — Typed Environment Configuration and Secret Boundaries.
Adheres to Pydantic V2 and Clean Architecture principles.
"""

from pathlib import Path
import tempfile
from typing import List, Literal, Optional
from urllib.parse import urlsplit, urlunsplit
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_default_db_path = Path(tempfile.gettempdir()) / "frs_dev.db"


def mask_database_url(url: str) -> str:
    """Masks user credentials in database URL to prevent credential leakage in logs or diagnostics."""
    try:
        parts = urlsplit(url)
        if parts.password:
            user = parts.username or ""
            host = parts.hostname or ""
            netloc = f"{user}:****@{host}"
            if parts.port:
                netloc += f":{parts.port}"
            return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
        return url
    except Exception:
        return "<masked_database_url>"


class Settings(BaseSettings):
    # Application identity
    APP_NAME: str = "FRS V7.1 K² Control Plane"
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # Server binding
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS & Hosts
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://k-squared-face-recognition-attendance-system-6rnfk44y10.vercel.app",
        "https://straddle-deflate-footwear.ngrok-free.dev",
    ]
    ALLOWED_HOSTS: List[str] = [
        "localhost",
        "127.0.0.1",
        "kucet.ac.in",
        "straddle-deflate-footwear.ngrok-free.dev",
    ]

    # Security & Tokens
    SECRET_KEY: str = Field(
        default="dev_insecure_secret_key_change_in_production_min_32_bytes_len",
        description="Cryptographic secret key for signing JWT tokens",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Persistence Store (Authoritative PostgreSQL in production; SQLite in dev/test)
    DATABASE_URL: str = Field(
        default=f"sqlite:///{_default_db_path.as_posix()}",
        description="Database connection string. PostgreSQL for production, SQLite for dev/test",
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_TIMEOUT_SECONDS: int = 30
    DATABASE_POOL_RECYCLE: int = 1800
    DATABASE_POOL_PRE_PING: bool = True

    # Supabase Cloud Persistence & Auth Integration
    SUPABASE_URL: Optional[str] = "https://hzqbgkdhxcnyakjjbjas.supabase.co"
    SUPABASE_KEY: Optional[str] = "sb_publishable_-7c2WIgh_dbXIewd-7-BAA_EDWdSiqZ"
    SUPABASE_SECRET_KEY: Optional[str] = Field(
        default=None,
        description="Supabase Service Role Secret Key (configured via environment, never hardcoded in source)",
    )

    # Firebase Authentication Integration
    FIREBASE_PROJECT_ID: Optional[str] = "k-squared-frs"
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None
    USE_FIREBASE_AUTH: bool = False

    # Cloudinary Object Storage for Images & Biometrics
    CLOUDINARY_CLOUD_NAME: Optional[str] = Field(default=None, description="Cloudinary cloud name / product environment")
    CLOUDINARY_API_KEY: Optional[str] = Field(default=None, description="Cloudinary API Key")
    CLOUDINARY_API_SECRET: Optional[str] = Field(default=None, description="Cloudinary API Secret")
    CLOUDINARY_URL: Optional[str] = Field(default=None, description="Cloudinary connection URL")
    IMAGE_STORAGE_PROVIDER: Literal["cloudinary", "local"] = "cloudinary"

    # Ingress & File Protection
    MAX_UPLOAD_SIZE_MB: int = 15
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png"]
    MAX_IMAGE_WIDTH: int = 4096
    MAX_IMAGE_HEIGHT: int = 4096
    STRIP_EXIF_METADATA: bool = True
    STORAGE_DIR: str = Field(
        default=str(Path(tempfile.gettempdir()) / "frs_storage" / "frames"),
        description="Path to shared frame storage accessible across backend API and vision worker containers",
    )

    # Vision Job Queue & Lease
    JOB_LEASE_TIMEOUT_SECONDS: int = 60
    JOB_MAX_RETRIES: int = 3
    JOB_POLL_INTERVAL_SECONDS: int = 2
    STRICT_CUDA_REQUIRED: bool = False

    # Observability
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "text"
    REDACT_SENSITIVE_LOGS: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def sync_database_url(self) -> str:
        """Returns synchronous database URL dialect compatible with SQLAlchemy 2.0 sync engine."""
        url = self.DATABASE_URL
        if url.startswith("postgresql+asyncpg://"):
            return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
        if url.startswith("sqlite+aiosqlite://"):
            return url.replace("sqlite+aiosqlite://", "sqlite://", 1)
        return url

    @property
    def masked_database_url(self) -> str:
        """Returns safe masked database URL string for logging and metrics."""
        return mask_database_url(self.DATABASE_URL)

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str, info) -> str:
        """Enforce strict persistence boundary: PostgreSQL required in production & staging."""
        env = info.data.get("ENVIRONMENT", "development")
        if env in ("production", "staging"):
            if "sqlite" in v.lower():
                raise ValueError(
                    f"CRITICAL ARCHITECTURE VIOLATION: SQLite database URL is forbidden in {env} mode. Authoritative PostgreSQL persistence is mandatory."
                )
            if not (v.startswith("postgresql://") or v.startswith("postgresql+") or v.startswith("postgres://")):
                raise ValueError(
                    f"CRITICAL CONFIGURATION ERROR: Invalid PostgreSQL connection scheme in {env} mode. Expected 'postgresql://' or 'postgresql+psycopg2://', got '{v}'"
                )
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Enforce strict fail-closed check for secret key in production."""
        env = info.data.get("ENVIRONMENT", "development")
        if env == "production":
            if "insecure" in v.lower() or len(v) < 32:
                raise ValueError(
                    "CRITICAL SECURITY FAILURE: In production mode, SECRET_KEY must be a cryptographically strong secret of at least 32 characters."
                )
        return v

    @field_validator("ALLOWED_HOSTS")
    @classmethod
    def validate_allowed_hosts(cls, v: List[str], info) -> List[str]:
        """Enforce strict host header validation: reject wildcard '*' in production."""
        env = info.data.get("ENVIRONMENT", "development")
        if env == "production" and ("*" in v or not v):
            raise ValueError(
                "CRITICAL SECURITY CONFIGURATION: Wildcard '*' in ALLOWED_HOSTS is strictly forbidden in production mode. Specify explicit domain hostnames."
            )
        return v


settings = Settings()

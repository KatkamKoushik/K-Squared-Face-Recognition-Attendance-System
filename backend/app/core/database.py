"""
K² FRS — Authoritative Persistence Engine & Database Session Management.
Supports PostgreSQL (Production) and SQLite (Development & Deterministic Testing).
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.core.config import settings


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy 2.0 ORM entities."""
    pass


# Connection pool configuration depends on target dialect
def build_engine(database_url: str, **custom_kwargs):
    """Builds a SQLAlchemy engine with dialect-specific pooling configuration."""
    kwargs = {"echo": settings.DEBUG}
    if "sqlite" in database_url:
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs["pool_size"] = settings.DATABASE_POOL_SIZE
        kwargs["max_overflow"] = settings.DATABASE_MAX_OVERFLOW
        kwargs["pool_timeout"] = settings.DATABASE_TIMEOUT_SECONDS
        kwargs["pool_recycle"] = settings.DATABASE_POOL_RECYCLE
        kwargs["pool_pre_ping"] = settings.DATABASE_POOL_PRE_PING
    kwargs.update(custom_kwargs)
    return create_engine(database_url, **kwargs)


engine = build_engine(settings.sync_database_url)

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a transactional session."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

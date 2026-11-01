"""
FRS V7.1 K² — PostgreSQL Bounded Queue Service.
Implements atomic lease claiming, heartbeat renewal, and safe recovery from worker crashes.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session
from app.core.config import settings
from app.domain.enums import JobState
from app.domain.models.job import VisionJob


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class QueueService:

    @staticmethod
    def claim_jobs(
        db: Session,
        worker_id: str,
        limit: int = 5,
    ) -> List[VisionJob]:
        """
        Atomically leases available or expired-lease jobs to a worker.
        """
        now = utc_now()
        lease_window = now + timedelta(seconds=settings.JOB_LEASE_TIMEOUT_SECONDS)

        stmt = (
            select(VisionJob)
            .where(
                and_(
                    VisionJob.attempt_count < VisionJob.max_attempts,
                    or_(
                        VisionJob.status == JobState.PENDING,
                        and_(
                            VisionJob.status.in_([JobState.LEASED, JobState.RUNNING]),
                            VisionJob.lease_expires_at < now,
                        ),
                    ),
                )
            )
            .order_by(VisionJob.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        jobs = list(db.execute(stmt).scalars().all())

        claimed_jobs: List[VisionJob] = []
        for job in jobs:
            job.status = JobState.LEASED
            job.worker_id = worker_id
            job.lease_expires_at = lease_window
            job.attempt_count += 1
            claimed_jobs.append(job)

        if claimed_jobs:
            db.flush()

        return claimed_jobs

    @staticmethod
    def heartbeat(db: Session, job_id: str, worker_id: str) -> bool:
        """Renews active lease on long-running vision inference."""
        now = utc_now()
        stmt = select(VisionJob).where(
            and_(
                VisionJob.id == job_id,
                VisionJob.worker_id == worker_id,
                VisionJob.status.in_([JobState.LEASED, JobState.RUNNING]),
            )
        )
        job = db.execute(stmt).scalar_one_or_none()
        if not job:
            return False

        job.status = JobState.RUNNING
        job.lease_expires_at = now + timedelta(seconds=settings.JOB_LEASE_TIMEOUT_SECONDS)
        db.flush()
        return True

    @staticmethod
    def complete_job(
        db: Session,
        job_id: str,
        worker_id: str,
        success: bool,
        error_message: Optional[str] = None,
    ) -> VisionJob:
        """Marks a job terminal success or failure."""
        stmt = select(VisionJob).where(
            and_(VisionJob.id == job_id, VisionJob.worker_id == worker_id)
        )
        job = db.execute(stmt).scalar_one_or_none()
        if not job:
            raise ValueError(f"Job {job_id} not claimed by worker {worker_id}")

        if success:
            job.status = JobState.SUCCEEDED
            job.error_message = None
        else:
            if job.attempt_count >= job.max_attempts:
                job.status = JobState.TERMINAL_FAILURE
            else:
                job.status = JobState.RETRYABLE_FAILURE
            job.error_message = error_message

        job.lease_expires_at = None
        db.flush()
        return job

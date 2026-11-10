"""
FRS V7.1 K² — Supabase Linter & Security Advisor Clean-up Migration.
1. Removes duplicate index on enrollment_submissions (idx_submission_roll).
2. Drops wide-open public RLS policies to eliminate 'RLS Policy Always True' warnings.
3. Keeps RLS enabled on all 29 tables; backend connects as postgres/service_role which bypasses RLS safely.
4. Moves vector extension to 'extensions' schema if applicable.
"""

import logging
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

import sqlalchemy as sa
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("supabase_cleaner")


def run_cleanup():
    logger.info("Connecting to Supabase at: %s", settings.masked_database_url)
    engine = sa.create_engine(settings.sync_database_url)

    with engine.begin() as conn:
        # 1. Drop duplicate index on enrollment_submissions
        logger.info("Dropping duplicate index on enrollment_submissions...")
        conn.execute(sa.text("DROP INDEX IF EXISTS public.idx_submission_roll;"))

        # 2. Drop the 29 open policies that flagged 'RLS Policy Always True'
        pols = conn.execute(
            sa.text("SELECT tablename, policyname FROM pg_policies WHERE schemaname = 'public'")
        ).fetchall()
        logger.info("Found %d policies to clean up.", len(pols))
        for tablename, policyname in pols:
            if policyname.startswith("allow_all_internal_"):
                logger.info("Dropping open policy %s on %s...", policyname, tablename)
                conn.execute(sa.text(f'DROP POLICY IF EXISTS "{policyname}" ON public."{tablename}";'))

        # 3. Create schema extensions if not exists and move vector extension
        try:
            conn.execute(sa.text("CREATE SCHEMA IF NOT EXISTS extensions;"))
            conn.execute(sa.text("ALTER EXTENSION vector SET SCHEMA extensions;"))
            logger.info("Moved vector extension to extensions schema.")
        except Exception as e:
            logger.warning("Notice on moving vector extension: %s", e)

        # 4. Confirm RLS remains ENABLED on all 29 tables
        tables = conn.execute(
            sa.text("SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
        ).fetchall()
        logger.info("Current RLS status on %d tables:", len(tables))
        for t, rls in tables:
            if not rls:
                conn.execute(sa.text(f'ALTER TABLE public."{t}" ENABLE ROW LEVEL SECURITY;'))
            logger.info("  %s: RLS enabled", t)

    logger.info("Supabase cleanup completed successfully.")


if __name__ == "__main__":
    run_cleanup()


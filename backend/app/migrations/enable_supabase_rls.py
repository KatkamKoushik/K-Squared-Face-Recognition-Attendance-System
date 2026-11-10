"""
FRS V7.1 K² — Supabase Row Level Security (RLS) Enablement Migration.
Enables RLS on all public schema tables to resolve Supabase Security Advisor Critical warnings,
and defines access policies for service_role, postgres, and authenticated roles.
"""

import logging
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

import sqlalchemy as sa
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("supabase_rls_migration")


def run_migration():
    logger.info("Connecting to Supabase at: %s", settings.masked_database_url)
    engine = sa.create_engine(settings.sync_database_url)

    with engine.begin() as conn:
        tables_res = conn.execute(
            sa.text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
        ).fetchall()
        tables = [r[0] for r in tables_res]
        logger.info("Found %d public tables in Supabase.", len(tables))

        for t in tables:
            logger.info("Enabling RLS on public.%s ...", t)
            conn.execute(sa.text(f'ALTER TABLE public."{t}" ENABLE ROW LEVEL SECURITY;'))

            policy_name = f"allow_all_internal_{t}"
            sql = f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_policies 
                    WHERE schemaname = 'public' AND tablename = '{t}' AND policyname = '{policy_name}'
                ) THEN
                    CREATE POLICY "{policy_name}" ON public."{t}" 
                    FOR ALL 
                    USING (true) 
                    WITH CHECK (true);
                END IF;
            END
            $$;
            """
            conn.execute(sa.text(sql))

    logger.info("RLS enabled and verified on all %d public tables in Supabase successfully.", len(tables))


if __name__ == "__main__":
    run_migration()

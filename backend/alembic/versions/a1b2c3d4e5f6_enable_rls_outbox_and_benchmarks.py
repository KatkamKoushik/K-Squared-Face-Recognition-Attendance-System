"""enable rls on outbox_events and ai_agent_evaluation_benchmarks

Revision ID: a1b2c3d4e5f6
Revises: 9a06bb2c4d3e
Create Date: 2026-11-27 18:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '9a06bb2c4d3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE IF EXISTS public.outbox_events ENABLE ROW LEVEL SECURITY;")
        op.execute("ALTER TABLE IF EXISTS public.ai_agent_evaluation_benchmarks ENABLE ROW LEVEL SECURITY;")
        op.execute("""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_policies WHERE tablename = 'outbox_events' AND policyname = 'service_role_all'
                    ) THEN
                        CREATE POLICY service_role_all ON public.outbox_events FOR ALL TO service_role USING (true) WITH CHECK (true);
                    END IF;
                    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'ai_agent_evaluation_benchmarks') THEN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_policies WHERE tablename = 'ai_agent_evaluation_benchmarks' AND policyname = 'service_role_all'
                        ) THEN
                            CREATE POLICY service_role_all ON public.ai_agent_evaluation_benchmarks FOR ALL TO service_role USING (true) WITH CHECK (true);
                        END IF;
                    END IF;
                END IF;
            END $$;
        """)


def downgrade() -> None:
    pass

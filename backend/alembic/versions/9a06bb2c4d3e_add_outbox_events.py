"""add outbox events table

Revision ID: 9a06bb2c4d3e
Revises: 8f95aa1b2c3d
Create Date: 2026-11-14 17:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a06bb2c4d3e'
down_revision: Union[str, None] = '8f95aa1b2c3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "outbox_events" not in tables:
        op.create_table(
            "outbox_events",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("event_type", sa.String(length=50), nullable=False, index=True),
            sa.Column("channel", sa.String(length=100), nullable=False, index=True),
            sa.Column("payload", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("idx_outbox_channel_created", "outbox_events", ["channel", "created_at"])
        op.create_index("idx_outbox_pending_events", "outbox_events", ["is_published", "created_at"])

        if bind.dialect.name == "postgresql":
            op.execute("ALTER TABLE outbox_events ENABLE ROW LEVEL SECURITY;")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "outbox_events" in tables:
        op.drop_table("outbox_events")

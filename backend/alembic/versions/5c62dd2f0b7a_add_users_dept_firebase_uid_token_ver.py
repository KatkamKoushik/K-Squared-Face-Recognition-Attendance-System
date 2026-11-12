"""add_users_dept_firebase_uid_token_ver

Revision ID: 5c62dd2f0b7a
Revises: 4b51cc1e9e8f
Create Date: 2026-11-12 22:43:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c62dd2f0b7a'
down_revision: Union[str, None] = '4b51cc1e9e8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_cols = {c['name'] for c in inspector.get_columns('users')}
    existing_indexes = {idx['name'] for idx in inspector.get_indexes('users')}
    existing_fks = {fk['name'] for fk in inspector.get_foreign_keys('users') if fk.get('name')}

    with op.batch_alter_table('users', schema=None) as batch_op:
        if 'firebase_uid' not in existing_cols:
            batch_op.add_column(sa.Column('firebase_uid', sa.String(length=128), nullable=True))
        if 'department_id' not in existing_cols:
            batch_op.add_column(sa.Column('department_id', sa.String(length=36), nullable=True))
        if 'token_version' not in existing_cols:
            batch_op.add_column(sa.Column('token_version', sa.Integer(), server_default='1', nullable=False))

        if 'fk_users_department_id' not in existing_fks and not any(
            fk.get('referred_table') == 'departments' for fk in inspector.get_foreign_keys('users')
        ):
            batch_op.create_foreign_key(
                'fk_users_department_id',
                'departments',
                ['department_id'],
                ['id'],
            )
        if 'ix_users_firebase_uid' not in existing_indexes:
            batch_op.create_index('ix_users_firebase_uid', ['firebase_uid'], unique=True)
        if 'ix_users_department_id' not in existing_indexes:
            batch_op.create_index('ix_users_department_id', ['department_id'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_cols = {c['name'] for c in inspector.get_columns('users')}
    existing_indexes = {idx['name'] for idx in inspector.get_indexes('users')}
    existing_fks = {fk['name'] for fk in inspector.get_foreign_keys('users') if fk.get('name')}

    with op.batch_alter_table('users', schema=None) as batch_op:
        if 'ix_users_department_id' in existing_indexes:
            batch_op.drop_index('ix_users_department_id')
        if 'ix_users_firebase_uid' in existing_indexes:
            batch_op.drop_index('ix_users_firebase_uid')
        if 'fk_users_department_id' in existing_fks:
            batch_op.drop_constraint('fk_users_department_id', type_='foreignkey')
        if 'token_version' in existing_cols:
            batch_op.drop_column('token_version')
        if 'department_id' in existing_cols:
            batch_op.drop_column('department_id')
        if 'firebase_uid' in existing_cols:
            batch_op.drop_column('firebase_uid')

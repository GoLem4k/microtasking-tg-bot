"""add ban user status

Revision ID: c7b3f9d2a1e4
Revises: b1f8a7e1c2d3
Create Date: 2026-04-01 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c7b3f9d2a1e4'
down_revision: Union[str, Sequence[str], None] = 'b1f8a7e1c2d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


old_status = sa.Enum('USER', 'ADMIN', name='user_status')
new_status = sa.Enum('USER', 'ADMIN', 'BAN', name='user_status')


def upgrade() -> None:
    op.alter_column(
        'users',
        'status',
        existing_type=old_status,
        type_=new_status,
        existing_nullable=False,
    )


def downgrade() -> None:
    op.execute("UPDATE users SET status = 'USER' WHERE status = 'BAN'")
    op.alter_column(
        'users',
        'status',
        existing_type=new_status,
        type_=old_status,
        existing_nullable=False,
    )

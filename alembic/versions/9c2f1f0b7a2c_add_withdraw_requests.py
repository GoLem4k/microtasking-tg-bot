"""add withdraw requests

Revision ID: 9c2f1f0b7a2c
Revises: 8c1d8e5c7f1b
Create Date: 2026-04-01 04:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '9c2f1f0b7a2c'
down_revision: Union[str, Sequence[str], None] = '8c1d8e5c7f1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'withdraw_requests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('method', sa.String(length=50), nullable=False),
        sa.Column('requisites', sa.String(length=255), nullable=True),
        sa.Column('currency', sa.String(length=50), nullable=True),
        sa.Column('amount', sa.BigInteger(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='withdraw_request_status'), nullable=False),
        sa.Column('admin_comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_withdraw_requests_user_id'), 'withdraw_requests', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_withdraw_requests_user_id'), table_name='withdraw_requests')
    op.drop_table('withdraw_requests')

"""add support requests

Revision ID: 8c1d8e5c7f1b
Revises: 5926adfc86c1
Create Date: 2026-04-01 03:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c1d8e5c7f1b'
down_revision: Union[str, Sequence[str], None] = '5926adfc86c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'support_requests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('message_text', sa.Text(), nullable=False),
        sa.Column('is_viewed', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_support_requests_user_id'), 'support_requests', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_support_requests_user_id'), table_name='support_requests')
    op.drop_table('support_requests')

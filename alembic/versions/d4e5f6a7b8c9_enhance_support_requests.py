"""enhance support requests

Revision ID: d4e5f6a7b8c9
Revises: c7b3f9d2a1e4
Create Date: 2026-04-01 12:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c7b3f9d2a1e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


support_status = sa.Enum('open', 'answered', 'deleted', name='support_request_status')


def upgrade() -> None:
    bind = op.get_bind()
    support_status.create(bind, checkfirst=True)

    op.add_column('support_requests', sa.Column('status', support_status, nullable=False, server_default='open'))
    op.add_column('support_requests', sa.Column('admin_reply', sa.Text(), nullable=True))
    op.add_column('support_requests', sa.Column('answered_by', sa.BigInteger(), nullable=True))
    op.add_column('support_requests', sa.Column('replied_at', sa.DateTime(), nullable=True))
    op.create_foreign_key(
        'fk_support_requests_answered_by_users',
        'support_requests',
        'users',
        ['answered_by'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint('fk_support_requests_answered_by_users', 'support_requests', type_='foreignkey')
    op.drop_column('support_requests', 'replied_at')
    op.drop_column('support_requests', 'answered_by')
    op.drop_column('support_requests', 'admin_reply')
    op.drop_column('support_requests', 'status')

    bind = op.get_bind()
    support_status.drop(bind, checkfirst=True)

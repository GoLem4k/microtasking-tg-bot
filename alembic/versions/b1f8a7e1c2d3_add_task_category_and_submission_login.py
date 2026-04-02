"""add task category and submission login

Revision ID: b1f8a7e1c2d3
Revises: 9c2f1f0b7a2c
Create Date: 2026-04-01 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1f8a7e1c2d3'
down_revision: Union[str, Sequence[str], None] = '9c2f1f0b7a2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    task_category = sa.Enum('MAIN', 'EXTRA', name='task_category')
    task_category.create(op.get_bind(), checkfirst=True)

    op.add_column(
        'tasks',
        sa.Column('category', task_category, nullable=False, server_default='MAIN'),
    )
    op.alter_column('tasks', 'category', server_default=None)

    op.add_column(
        'task_submissions',
        sa.Column('performer_login', sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('task_submissions', 'performer_login')
    op.drop_column('tasks', 'category')

    task_category = sa.Enum('MAIN', 'EXTRA', name='task_category')
    task_category.drop(op.get_bind(), checkfirst=True)

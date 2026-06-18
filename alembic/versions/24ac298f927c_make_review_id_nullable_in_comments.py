
"""make review_id nullable in comments

Revision ID: 24ac298f927c
Revises: f7071f7630d2
Create Date: 2026-06-09 19:24:50.690350

"""
from typing import Sequence, Union
import sqlalchemy as sa
import sqlmodel
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '24ac298f927c'
down_revision: Union[str, Sequence[str], None] = 'f7071f7630d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('comments') as batch_op:
        batch_op.alter_column('review_id', existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table('comments') as batch_op:
        batch_op.alter_column('review_id', existing_type=sa.Integer(), nullable=False)


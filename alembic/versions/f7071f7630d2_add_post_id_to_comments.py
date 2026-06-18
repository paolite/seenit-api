
"""add post_id to comments

Revision ID: f7071f7630d2
Revises: f16ca48dd0b8
Create Date: 2026-06-08 17:39:51.037829

"""
from typing import Sequence, Union
import sqlalchemy as sa
import sqlmodel
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7071f7630d2'
down_revision: Union[str, Sequence[str], None] = 'f16ca48dd0b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('comments', sa.Column('post_id', sa.Integer(), nullable=True))
    op.create_foreign_key('comments_post_id_fkey', 'comments', 'posts', ['post_id'], ['id'])

def downgrade() -> None:
    op.drop_constraint('comments_post_id_fkey', 'comments', type_='foreignkey')
    op.drop_column('comments', 'post_id')


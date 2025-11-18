"""add content to boletin instance

Revision ID: d3e5f6a7b8c2
Revises: c8f9e4d2b5a1
Create Date: 2025-11-18 02:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd3e5f6a7b8c2'
down_revision: Union[str, None] = 'c8f9e4d2b5a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add content column to boletin_instances
    op.add_column('boletin_instances', sa.Column('content', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove content column from boletin_instances
    op.drop_column('boletin_instances', 'content')

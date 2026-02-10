"""add num_semanas to boletin_instances

Revision ID: a116b87fea0b
Revises: 30924f92d5e7
Create Date: 2026-02-10 10:08:21.957390

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel  # Always import sqlmodel for SQLModel types
import geoalchemy2  # Required for Geometry types


# revision identifiers, used by Alembic.
revision: str = 'a116b87fea0b'
down_revision: Union[str, Sequence[str], None] = '30924f92d5e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('boletin_instances', sa.Column('num_semanas', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('boletin_instances', 'num_semanas')

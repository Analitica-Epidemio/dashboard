"""add boletin_metadata to boletin_template_config

Revision ID: 4368520b7836
Revises: a116b87fea0b
Create Date: 2026-02-13 23:08:39.895143

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel  # Always import sqlmodel for SQLModel types
import geoalchemy2  # Required for Geometry types


# revision identifiers, used by Alembic.
revision: str = '4368520b7836'
down_revision: Union[str, Sequence[str], None] = 'a116b87fea0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('boletin_template_config', sa.Column('boletin_metadata', sa.JSON(), server_default='{}', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('boletin_template_config', 'boletin_metadata')

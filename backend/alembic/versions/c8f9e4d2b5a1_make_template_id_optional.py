"""make template_id optional

Revision ID: c8f9e4d2b5a1
Revises: abafaf850330
Create Date: 2025-11-18 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8f9e4d2b5a1'
down_revision: Union[str, None] = 'abafaf850330'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make template_id nullable
    op.alter_column('boletin_instances', 'template_id',
               existing_type=sa.INTEGER(),
               nullable=True)


def downgrade() -> None:
    # Make template_id not nullable again
    op.alter_column('boletin_instances', 'template_id',
               existing_type=sa.INTEGER(),
               nullable=False)

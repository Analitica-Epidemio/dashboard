"""update_codigo_snvs_length

Revision ID: 11a2fa233d31
Revises: cee395b9bdf2
Create Date: 2025-11-07 18:48:00.451307

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel  # Always import sqlmodel for SQLModel types
import geoalchemy2  # Required for Geometry types


# revision identifiers, used by Alembic.
revision: str = '11a2fa233d31'
down_revision: Union[str, Sequence[str], None] = 'cee395b9bdf2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Cambiar codigo_snvs de VARCHAR(50) a VARCHAR(20)
    # Porque codigo_snvs ahora guarda IDs (números), no nombres largos
    op.alter_column('establecimiento', 'codigo_snvs',
                    type_=sa.String(length=20),
                    existing_type=sa.String(length=50),
                    existing_nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Revertir a VARCHAR(50)
    op.alter_column('establecimiento', 'codigo_snvs',
                    type_=sa.String(length=50),
                    existing_type=sa.String(length=20),
                    existing_nullable=True)

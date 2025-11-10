"""add establecimiento mapeo tracking

Revision ID: 254d67b5cc6f
Revises: 11a2fa233d31
Create Date: 2025-11-07 21:16:49.733994

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel  # Always import sqlmodel for SQLModel types
import geoalchemy2  # Required for Geometry types


# revision identifiers, used by Alembic.
revision: str = '254d67b5cc6f'
down_revision: Union[str, Sequence[str], None] = '11a2fa233d31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Agregar campos a establecimiento para metadata de mapeo
    op.add_column('establecimiento', sa.Column('mapeo_validado', sa.Boolean(), nullable=True,
                                                comment='Si el mapeo SNVS→IGN fue validado manualmente'))
    op.add_column('establecimiento', sa.Column('mapeo_confianza', sa.String(length=20), nullable=True,
                                                comment='Nivel de confianza del mapeo: HIGH, MEDIUM, LOW'))
    op.add_column('establecimiento', sa.Column('mapeo_score', sa.Float(), nullable=True,
                                                comment='Score de similitud del mapeo (0-100)'))
    op.add_column('establecimiento', sa.Column('mapeo_similitud_nombre', sa.Float(), nullable=True,
                                                comment='Similitud de nombre del mapeo (0-100)'))
    op.add_column('establecimiento', sa.Column('mapeo_razon', sa.Text(), nullable=True,
                                                comment='Razón/descripción del mapeo'))
    op.add_column('establecimiento', sa.Column('mapeo_es_manual', sa.Boolean(), nullable=True,
                                                comment='Si el mapeo fue creado manualmente o automático'))


def downgrade() -> None:
    """Downgrade schema."""
    # Eliminar columnas de establecimiento
    op.drop_column('establecimiento', 'mapeo_es_manual')
    op.drop_column('establecimiento', 'mapeo_razon')
    op.drop_column('establecimiento', 'mapeo_similitud_nombre')
    op.drop_column('establecimiento', 'mapeo_score')
    op.drop_column('establecimiento', 'mapeo_confianza')
    op.drop_column('establecimiento', 'mapeo_validado')

"""change geocodificado to estado_geocodificacion enum

Revision ID: 5f5344038a56
Revises: 7f74d379f63f
Create Date: 2025-10-28 17:14:08.682492

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel  # Always import sqlmodel for SQLModel types
import geoalchemy2  # Required for Geometry types


# revision identifiers, used by Alembic.
revision: str = '5f5344038a56'
down_revision: Union[str, Sequence[str], None] = '7f74d379f63f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Crear el tipo ENUM en PostgreSQL
    estado_geocodificacion_enum = sa.Enum(
        'PENDIENTE', 'EN_COLA', 'PROCESANDO', 'GEOCODIFICADO',
        'FALLO_TEMPORAL', 'FALLO_PERMANENTE', 'NO_GEOCODIFICABLE', 'DESHABILITADO',
        name='estadogeocodificacion'
    )
    estado_geocodificacion_enum.create(op.get_bind(), checkfirst=True)

    # Agregar nuevas columnas
    op.add_column('domicilio', sa.Column('estado_geocodificacion', estado_geocodificacion_enum, nullable=True))
    op.add_column('domicilio', sa.Column('intentos_geocodificacion', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('domicilio', sa.Column('ultimo_error_geocodificacion', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True))

    # Migrar datos existentes: geocodificado=true -> GEOCODIFICADO, geocodificado=false -> PENDIENTE
    op.execute("""
        UPDATE domicilio
        SET estado_geocodificacion = CASE
            WHEN geocodificado = true THEN 'GEOCODIFICADO'::estadogeocodificacion
            ELSE 'PENDIENTE'::estadogeocodificacion
        END
    """)

    # Hacer la columna NOT NULL después de migrar los datos
    op.alter_column('domicilio', 'estado_geocodificacion', nullable=False)

    # Eliminar columna vieja
    op.drop_column('domicilio', 'geocodificado')

    # Remover default de intentos_geocodificacion
    op.alter_column('domicilio', 'intentos_geocodificacion', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    # Agregar columna vieja
    op.add_column('domicilio', sa.Column('geocodificado', sa.BOOLEAN(), autoincrement=False, nullable=True))

    # Migrar datos de vuelta: GEOCODIFICADO -> true, otros -> false
    op.execute("""
        UPDATE domicilio
        SET geocodificado = CASE
            WHEN estado_geocodificacion = 'GEOCODIFICADO' THEN true
            ELSE false
        END
    """)

    # Hacer NOT NULL
    op.alter_column('domicilio', 'geocodificado', nullable=False)

    # Eliminar nuevas columnas
    op.drop_column('domicilio', 'ultimo_error_geocodificacion')
    op.drop_column('domicilio', 'intentos_geocodificacion')
    op.drop_column('domicilio', 'estado_geocodificacion')

    # Eliminar el tipo ENUM
    sa.Enum(name='estadogeocodificacion').drop(op.get_bind(), checkfirst=True)

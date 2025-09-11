"""add_charts_tables

Revision ID: 2684e4eb2feb
Revises: a19cd800a9c4
Create Date: 2025-09-11 12:13:15.188128

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel  # Always import sqlmodel for SQLModel types


# revision identifiers, used by Alembic.
revision: str = '2684e4eb2feb'
down_revision: Union[str, Sequence[str], None] = 'a19cd800a9c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create dashboard_chart table
    op.create_table(
        'dashboard_chart',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('codigo', sa.String(length=50), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('funcion_procesamiento', sa.String(length=100), nullable=False),
        sa.Column('condiciones_display', sa.JSON(), nullable=True),
        sa.Column('tipo_visualizacion', sa.String(length=50), nullable=False),
        sa.Column('configuracion_chart', sa.JSON(), nullable=True),
        sa.Column('orden', sa.Integer(), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dashboard_chart_codigo'), 'dashboard_chart', ['codigo'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_dashboard_chart_codigo'), table_name='dashboard_chart')
    op.drop_table('dashboard_chart')

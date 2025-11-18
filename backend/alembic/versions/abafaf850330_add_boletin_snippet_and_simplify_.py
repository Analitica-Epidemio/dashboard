"""add_boletin_snippet_and_simplify_template

Revision ID: abafaf850330
Revises: 0d99c2efa49a
Create Date: 2025-11-17 21:54:04.558244

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel  # Always import sqlmodel for SQLModel types
import geoalchemy2  # Required for Geometry types


# revision identifiers, used by Alembic.
revision: str = 'abafaf850330'
down_revision: Union[str, Sequence[str], None] = '0d99c2efa49a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade schema:
    1. Create boletin_snippets table
    2. Remove layout, widgets, thumbnail, and global_filters from boletin_templates
    3. Delete existing boletin template records (cleanup)
    """
    # 1. Create boletin_snippets table
    op.create_table(
        'boletin_snippets',
        sa.Column('codigo', sa.String(length=100), nullable=False),
        sa.Column('nombre', sa.String(length=255), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('categoria', sa.String(length=50), nullable=False),
        sa.Column('template', sa.Text(), nullable=False),
        sa.Column('variables_schema', sa.JSON(), nullable=False),
        sa.Column('condiciones', sa.JSON(), nullable=True),
        sa.Column('orden', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        # Base model fields (from BaseModel)
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('codigo')
    )
    op.create_index('ix_boletin_snippets_codigo', 'boletin_snippets', ['codigo'])
    op.create_index('ix_boletin_snippets_categoria', 'boletin_snippets', ['categoria'])

    # 2. Delete existing boletin template records (cleanup per user request)
    op.execute("DELETE FROM boletin_templates")

    # 3. Remove deprecated columns from boletin_templates
    op.drop_column('boletin_templates', 'layout')
    op.drop_column('boletin_templates', 'widgets')
    op.drop_column('boletin_templates', 'thumbnail')
    op.drop_column('boletin_templates', 'global_filters')


def downgrade() -> None:
    """
    Downgrade schema:
    1. Re-add removed columns to boletin_templates
    2. Drop boletin_snippets table
    """
    # 1. Re-add removed columns to boletin_templates
    op.add_column('boletin_templates', sa.Column('layout', sa.JSON(), nullable=False, server_default='{}'))
    op.add_column('boletin_templates', sa.Column('widgets', sa.JSON(), nullable=False, server_default='[]'))
    op.add_column('boletin_templates', sa.Column('thumbnail', sa.String(length=500), nullable=True))
    op.add_column('boletin_templates', sa.Column('global_filters', sa.JSON(), nullable=True))

    # 2. Drop boletin_snippets table
    op.drop_index('ix_boletin_snippets_categoria', 'boletin_snippets')
    op.drop_index('ix_boletin_snippets_codigo', 'boletin_snippets')
    op.drop_table('boletin_snippets')

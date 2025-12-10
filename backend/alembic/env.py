# type: ignore
"""
Alembic environment configuration for Sistema de Epidemiología.

Configuración de migrations con SQLModel y AsyncIO support.
"""

import os

# Importar configuración de la aplicación
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Importar SQLModel
# Importar helpers de GeoAlchemy2 para Alembic
from geoalchemy2 import alembic_helpers
from sqlmodel import SQLModel

from app.core.config import settings

# Importar todos los modelos para que Alembic los detecte
# IMPORTANTE: Importar todos los modelos de los dominios aquí
from app.domains import *  # noqa: F403, F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_database_url() -> str:
    """
    Obtiene la URL de la base de datos desde las configuraciones.

    Returns:
        URL de conexión a la base de datos
    """
    return settings.DATABASE_URL


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Configuración para PostgreSQL
        render_as_batch=False,
        compare_type=True,
        compare_server_default=True,
        # GeoAlchemy2 helpers
        include_object=include_object,
        process_revision_directives=alembic_helpers.writer,
        render_item=alembic_helpers.render_item,
    )

    with context.begin_transaction():
        context.run_migrations()


def include_object(object, name, type_, reflected, compare_to):
    """
    Determina qué objetos de la base de datos incluir en autogenerate.

    Combina la lógica de GeoAlchemy2 con filtros personalizados para
    excluir tablas de PostGIS y Tiger Geocoder.
    """
    # Primero, aplicar la lógica de GeoAlchemy2
    if not alembic_helpers.include_object(object, name, type_, reflected, compare_to):
        return False

    # Luego, aplicar nuestra lógica personalizada
    if type_ == "table":
        # Tablas de PostGIS/Tiger Geocoder a ignorar
        postgis_tables = {
            # PostGIS core
            "spatial_ref_sys",
            "topology",
            "layer",
            # Tiger Geocoder
            "faces",
            "edges",
            "addr",
            "addrfeat",
            "featnames",
            "place",
            "county",
            "state",
            "tract",
            "bg",
            "cousub",
            "tabblock",
            "tabblock20",
            "zcta5",
            # Lookups
            "county_lookup",
            "place_lookup",
            "direction_lookup",
            "street_type_lookup",
            "secondary_unit_lookup",
            "state_lookup",
            "countysub_lookup",
            "zip_lookup",
            "zip_lookup_base",
            "zip_lookup_all",
            "zip_state",
            "zip_state_loc",
            # PAGC (address standardization)
            "pagc_gaz",
            "pagc_lex",
            "pagc_rules",
            # Loader
            "loader_platform",
            "loader_variables",
            "loader_lookuptables",
            # Geocoding
            "geocode_settings",
            "geocode_settings_default",
        }
        if name.lower() in postgis_tables:
            return False

    return True


def do_run_migrations(connection: Connection) -> None:
    """
    Ejecuta las migrations con una conexión existente.

    Args:
        connection: Conexión a la base de datos
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # Configuraciones específicas para epidemiología
        render_as_batch=False,
        compare_type=True,
        compare_server_default=True,
        # Incluir esquemas si es necesario
        include_schemas=True,
        # Configuración para timestamps y UUIDs
        user_module_prefix="sqlalchemy_utils.",
        # GeoAlchemy2 helpers para manejo correcto de geometrías
        include_object=include_object,
        process_revision_directives=alembic_helpers.writer,
        render_item=alembic_helpers.render_item,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in 'online' mode usando AsyncIO.

    En este escenario necesitamos crear un Engine
    y asociar una conexión con el contexto.
    """
    # Configuración del engine asíncrono
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    En este escenario necesitamos crear un Engine
    y asociar una conexión con el contexto.
    """
    # Para compatibilidad, también soportamos modo síncrono
    from sqlalchemy import create_engine

    url = get_database_url()

    # Convertir URL async a sync si es necesario para migrations
    if url.startswith("postgresql+asyncpg://"):
        sync_url = url.replace("postgresql+asyncpg://", "postgresql://")
    else:
        sync_url = url

    connectable = create_engine(
        sync_url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=False,
            compare_type=True,
            compare_server_default=True,
            # Ignorar tablas de PostGIS/Tiger
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


# Determinar si ejecutar en modo async u online
if context.is_offline_mode():
    run_migrations_offline()
else:
    # Por defecto usar modo síncrono para migrations
    # AsyncIO puede causar problemas con algunas versiones de Alembic
    run_migrations_online()

"""Configuración de la base de datos."""

from typing import AsyncGenerator, Generator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings

# Para desarrollo, usar engines síncrono y asíncrono
database_url_sync = settings.DATABASE_URL.replace(
    "postgresql+asyncpg://", "postgresql://"
)
database_url_async = settings.DATABASE_URL

# Crear engines
engine = create_engine(database_url_sync, echo=False)

async_engine = create_async_engine(database_url_async, echo=False)


def get_session() -> Generator[Session, None, None]:
    """Obtiene una sesión de base de datos."""
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Obtiene una sesión asíncrona de base de datos."""
    async with AsyncSession(async_engine) as session:
        yield session


def create_db_and_tables() -> None:
    """Crea las tablas de la base de datos."""
    try:
        SQLModel.metadata.create_all(engine)
    except Exception as e:
        print(f"Warning: Could not create tables: {e}")
        # En desarrollo, es OK si no hay tablas aún

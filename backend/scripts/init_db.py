"""
Inicialización de base de datos.

Script para crear usuario admin inicial.
"""

import asyncio
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.auth.user import User
from app.core.config import settings
from app.core.database import async_engine, create_db_and_tables
from app.core.user_manager import UserManager, get_user_db

logger = logging.getLogger(__name__)


async def create_first_admin(session: AsyncSession) -> Optional[User]:
    """
    Crea el primer usuario administrador si no existe.

    Args:
        session: Sesión de base de datos

    Returns:
        Usuario admin creado o None si ya existe
    """
    # Verificar si ya existe un admin
    result = await session.execute(select(User).where(User.is_superuser.is_(True)))
    existing_admin = result.scalars().first()

    if existing_admin:
        logger.info("Ya existe un usuario administrador")
        return None

    # Crear admin
    admin_email = "admin@admin.com"
    admin_password = "admin"  # Cambiar en producción

    # Crear usuario directamente
    user_db = await anext(get_user_db(session))
    user_manager = UserManager(user_db)

    # Hash password
    hashed_password = user_manager.password_helper.hash(admin_password)

    # Crear modelo de usuario
    admin_user = User(
        email=admin_email,
        hashed_password=hashed_password,
        is_active=True,
        is_verified=True,
        is_superuser=True,
        nombre_completo="Administrador del Sistema",
    )

    session.add(admin_user)
    await session.commit()
    await session.refresh(admin_user)

    logger.info(f"Usuario administrador creado: {admin_email}")
    if settings.ENVIRONMENT == "development":
        logger.info(f"Password temporal: {admin_password}")

    return admin_user


async def init_db() -> None:
    """
    Inicializa la base de datos.

    - Crea tablas si no existen
    - Crea usuario admin inicial
    """
    logger.info("Inicializando base de datos...")

    # Crear tablas
    create_db_and_tables()

    # Crear admin
    async with AsyncSession(async_engine) as session:
        await create_first_admin(session)

    logger.info("Base de datos inicializada")


if __name__ == "__main__":
    asyncio.run(init_db())

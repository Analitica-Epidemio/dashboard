"""
Configuración de email para autenticación.
"""

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_reset_password_email(email: str, token: str) -> None:
    """
    Envía email de reset de password.

    Args:
        email: Email del usuario
        token: Token de reset
    """
    # TODO: Implementar envío real cuando se configure SMTP
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    # Log de auditoría (sin token por seguridad)
    logger.info(f"Reset password email generado para {email}")

    # En desarrollo, mostrar URL para testing (solo via logger.debug)
    if settings.ENVIRONMENT == "development":
        logger.debug(f"[DEV] Reset URL: {reset_url}")


async def send_verification_email(email: str, token: str) -> None:
    """
    Envía email de verificación.

    Args:
        email: Email del usuario
        token: Token de verificación
    """
    # TODO: Implementar envío real cuando se configure SMTP
    verify_url = f"{settings.FRONTEND_URL}/verify?token={token}"

    # Log de auditoría (sin token por seguridad)
    logger.info(f"Verification email generado para {email}")

    # En desarrollo, mostrar URL para testing (solo via logger.debug)
    if settings.ENVIRONMENT == "development":
        logger.debug(f"[DEV] Verify URL: {verify_url}")

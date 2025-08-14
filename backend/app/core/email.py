"""
Configuración de email para autenticación.
"""

import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_reset_password_email(email: str, token: str) -> None:
    """
    Envía email de reset de password.

    Args:
        email: Email del usuario
        token: Token de reset
    """
    # Por ahora solo log, implementar envío real cuando se configure SMTP
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    logger.info(f"Reset password email para {email}")
    logger.info(f"Reset URL: {reset_url}")

    if settings.ENVIRONMENT == "development":
        print(f"\n{'=' * 50}")
        print(f"RESET PASSWORD EMAIL")
        print(f"To: {email}")
        print(f"Reset URL: {reset_url}")
        print(f"Token: {token}")
        print(f"{'=' * 50}\n")


async def send_verification_email(email: str, token: str) -> None:
    """
    Envía email de verificación.

    Args:
        email: Email del usuario
        token: Token de verificación
    """
    # Por ahora solo log, implementar envío real cuando se configure SMTP
    verify_url = f"{settings.FRONTEND_URL}/verify?token={token}"

    logger.info(f"Verification email para {email}")
    logger.info(f"Verify URL: {verify_url}")

    if settings.ENVIRONMENT == "development":
        print(f"\n{'=' * 50}")
        print(f"VERIFICATION EMAIL")
        print(f"To: {email}")
        print(f"Verify URL: {verify_url}")
        print(f"Token: {token}")
        print(f"{'=' * 50}\n")

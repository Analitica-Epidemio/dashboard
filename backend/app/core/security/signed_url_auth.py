"""
Middleware para autenticación con URLs firmadas
"""

import logging
from typing import Optional

from fastapi import HTTPException, Request

from app.api.v1.reports.signed_url import verify_signed_url

logger = logging.getLogger(__name__)


async def verify_signed_url_headers(request: Request) -> Optional[dict]:
    """
    Verifica si la petición tiene headers de URL firmada válidos

    Returns:
        Dict con los datos verificados o None si no hay headers
    """
    signed_data = request.headers.get("X-Signed-Data")
    signed_signature = request.headers.get("X-Signed-Signature")

    logger.debug("Checking signed URL headers:")
    logger.debug(
        f"  X-Signed-Data: {'Present' if signed_data else 'Missing'} - {signed_data[:50] if signed_data else 'N/A'}..."
    )
    logger.debug(
        f"  X-Signed-Signature: {'Present' if signed_signature else 'Missing'} - {signed_signature[:20] if signed_signature else 'N/A'}..."
    )

    if not signed_data or not signed_signature:
        logger.debug("No signed URL headers found")
        return None

    try:
        # Verificar la URL firmada
        logger.debug(
            f"Verifying signed URL with data: {signed_data[:50]}... and signature: {signed_signature[:20]}..."
        )
        verified_data = verify_signed_url(signed_data, signed_signature)
        logger.info(
            f"✅ Signed URL verified successfully. User ID: {verified_data.get('generated_by')}"
        )
        return verified_data
    except ValueError as e:
        logger.error(f"❌ Signed URL verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))

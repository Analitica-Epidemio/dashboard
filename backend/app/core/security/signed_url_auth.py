"""
Middleware para autenticación con URLs firmadas
"""

from typing import Optional
from fastapi import HTTPException, Request
from app.api.v1.reports.signed_url import verify_signed_url


async def verify_signed_url_headers(request: Request) -> Optional[dict]:
    """
    Verifica si la petición tiene headers de URL firmada válidos

    Returns:
        Dict con los datos verificados o None si no hay headers
    """
    signed_data = request.headers.get("X-Signed-Data")
    signed_signature = request.headers.get("X-Signed-Signature")

    if not signed_data or not signed_signature:
        return None

    try:
        # Verificar la URL firmada
        verified_data = verify_signed_url(signed_data, signed_signature)
        return verified_data
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
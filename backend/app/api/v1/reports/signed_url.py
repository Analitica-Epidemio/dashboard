"""
Endpoint para generar URLs firmadas para reportes SSR
"""

import base64
import hashlib
import hmac
import json
import logging
import time
from datetime import date
from typing import Dict, List, Optional, TypedDict

from fastapi import Depends
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.schemas.response import SuccessResponse
from app.core.security.rbac import RequireAnyRole
from app.domains.autenticacion.models import User

logger = logging.getLogger(__name__)


class SignedUrlResult(TypedDict):
    """Resultado de generar una URL firmada"""

    signed_url: str
    expires_at: int


class ReportFiltersRequest(BaseModel):
    """Request para generar URL firmada"""

    filters: List[Dict] = Field(..., description="Lista de combinaciones de filtros")
    date_from: Optional[date] = Field(None, description="Fecha desde")
    date_to: Optional[date] = Field(None, description="Fecha hasta")
    expires_in: int = Field(
        3600, description="Tiempo de expiración en segundos", ge=60, le=86400
    )


class SignedUrlResponse(BaseModel):
    """Response con la URL firmada"""

    signed_url: str = Field(..., description="URL firmada para acceder al reporte")
    expires_at: int = Field(..., description="Timestamp de expiración")


class VerifySignedUrlRequest(BaseModel):
    """Request para verificar URL firmada"""

    data: str = Field(..., description="Payload codificado en base64")
    signature: str = Field(..., description="Firma HMAC")


class VerifySignedUrlResponse(BaseModel):
    """Response con los datos verificados"""

    filters: List[Dict] = Field(..., description="Lista de filtros verificados")
    date_from: Optional[str] = Field(None, description="Fecha desde")
    date_to: Optional[str] = Field(None, description="Fecha hasta")
    generated_by: int = Field(..., description="ID del usuario que generó la URL")
    generated_at: int = Field(..., description="Timestamp de generación")


def generate_signed_url(filters_data: Dict, expires_in: int = 3600) -> SignedUrlResult:
    """
    Genera una URL firmada para los filtros del reporte

    Args:
        filters_data: Datos de filtros a firmar
        expires_in: Tiempo de expiración en segundos

    Returns:
        Dict con signed_url y expires_at
    """
    # Crear payload con filtros y expiración
    expires_at = int(time.time()) + expires_in
    payload = {**filters_data, "expires_at": expires_at}

    # Serializar payload
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload_encoded = (
        base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")
    )

    # Generar firma HMAC
    secret_key = settings.SECRET_KEY.encode()
    signature = hmac.new(
        secret_key, payload_encoded.encode(), hashlib.sha256
    ).hexdigest()

    # Construir URL firmada
    signed_url = f"/reports-ssr?data={payload_encoded}&signature={signature}"

    return {"signed_url": signed_url, "expires_at": expires_at}


def verify_signed_url(data: str, signature: str) -> Dict:
    """
    Verifica una URL firmada y devuelve los filtros

    Args:
        data: Payload codificado en base64
        signature: Firma HMAC

    Returns:
        Dict con los filtros verificados

    Raises:
        ValueError: Si la firma es inválida o la URL expiró
    """
    try:
        # IMPORTANTE: Guardar el data original para verificar la firma
        original_data = data

        # Decodificar payload - añadir padding si es necesario
        missing_padding = len(data) % 4
        if missing_padding:
            data += "=" * (4 - missing_padding)

        payload_json = base64.urlsafe_b64decode(data.encode()).decode()
        payload = json.loads(payload_json)

        # Verificar expiración
        if time.time() > payload.get("expires_at", 0):
            logger.warning("Signed URL expired")
            raise ValueError("URL has expired")

        # Verificar firma usando el data ORIGINAL (sin padding añadido)
        secret_key = settings.SECRET_KEY.encode()
        expected_signature = hmac.new(
            secret_key,
            original_data.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            logger.warning("Signed URL signature mismatch")
            raise ValueError("Invalid signature")

        # Remover expires_at del payload antes de devolver
        payload.pop("expires_at", None)
        return payload

    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Invalid signed URL: {str(e)}")


async def generate_report_signed_url(
    request: ReportFiltersRequest, current_user: User = Depends(RequireAnyRole())
) -> SuccessResponse[SignedUrlResponse]:
    """
    Genera una URL firmada para acceder a un reporte SSR
    """
    # Preparar datos para firmar
    filters_data = {
        "filters": request.filters,
        "date_from": request.date_from.isoformat() if request.date_from else None,
        "date_to": request.date_to.isoformat() if request.date_to else None,
        "generated_by": current_user.id,  # Para auditoría
        "generated_at": int(time.time()),
    }

    # Generar URL firmada
    result = generate_signed_url(filters_data, request.expires_in)

    response = SignedUrlResponse(
        signed_url=result["signed_url"], expires_at=result["expires_at"]
    )

    return SuccessResponse(data=response)


async def verify_signed_url_endpoint(
    request: VerifySignedUrlRequest,
) -> SuccessResponse[VerifySignedUrlResponse]:
    """
    Verifica una URL firmada y devuelve los datos de filtros
    """
    try:
        # Verificar URL firmada
        verified_data = verify_signed_url(request.data, request.signature)

        response = VerifySignedUrlResponse(
            filters=verified_data["filters"],
            date_from=verified_data.get("date_from"),
            date_to=verified_data.get("date_to"),
            generated_by=verified_data["generated_by"],
            generated_at=verified_data["generated_at"],
        )

        return SuccessResponse(data=response)

    except ValueError as e:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail=str(e))

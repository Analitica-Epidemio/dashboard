"""Endpoint para aceptar múltiples sugerencias de mapeo en bulk."""

from typing import List, Dict
from fastapi import Depends
from sqlmodel import Session

from app.core.database import get_session
from .mapeo_schemas import AceptarSugerenciasBulkRequest
from .crear_mapeo import crear_mapeo_snvs_ign
from .mapeo_schemas import CrearMapeoRequest


async def aceptar_sugerencias_bulk(
    request: AceptarSugerenciasBulkRequest,
    session: Session = Depends(get_session),
) -> dict:
    """
    Acepta múltiples sugerencias de mapeo en una sola operación.

    Útil para aceptar todas las sugerencias de alta confianza de una vez.
    """
    resultados_exitosos = []
    resultados_fallidos = []

    for mapeo_request in request.mapeos:
        try:
            resultado = await crear_mapeo_snvs_ign(mapeo_request, session)
            resultados_exitosos.append({
                "id_establecimiento_snvs": mapeo_request.id_establecimiento_snvs,
                "id_establecimiento_ign": mapeo_request.id_establecimiento_ign,
                "status": "success",
                "data": resultado
            })
        except Exception as e:
            resultados_fallidos.append({
                "id_establecimiento_snvs": mapeo_request.id_establecimiento_snvs,
                "id_establecimiento_ign": mapeo_request.id_establecimiento_ign,
                "status": "error",
                "error": str(e)
            })

    return {
        "message": f"Procesados {len(request.mapeos)} mapeos",
        "exitosos": len(resultados_exitosos),
        "fallidos": len(resultados_fallidos),
        "resultados_exitosos": resultados_exitosos,
        "resultados_fallidos": resultados_fallidos
    }

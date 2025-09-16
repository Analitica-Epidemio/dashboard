"""
Get indicadores endpoint
"""

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAuthOrSignedUrl
from app.domains.autenticacion.models import User

logger = logging.getLogger(__name__)


class IndicadoresResponse(BaseModel):
    """Response model para indicadores del dashboard"""

    total_casos: int = Field(..., description="Total de casos registrados")
    tasa_incidencia: float = Field(..., description="Tasa de incidencia por 100.000 habitantes")
    areas_afectadas: int = Field(..., description="Número de departamentos afectados")
    letalidad: float = Field(..., description="Tasa de letalidad en porcentaje")
    filtros_aplicados: Dict[str, Any] = Field(..., description="Filtros que se aplicaron a la consulta")


async def get_indicadores(
    grupo_id: Optional[int] = Query(None, description="ID del grupo seleccionado"),
    evento_id: Optional[int] = Query(None, description="ID del evento seleccionado"),
    fecha_desde: Optional[date] = Query(None, description="Fecha desde (formato: YYYY-MM-DD)"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta (formato: YYYY-MM-DD)"),
    clasificaciones: Optional[List[str]] = Query(None, description="Filtrar por clasificaciones estratégicas"),
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = RequireAuthOrSignedUrl
) -> SuccessResponse[IndicadoresResponse]:
    """
    Obtiene los indicadores de resumen para el dashboard

    Calcula:
    - Total de casos
    - Tasa de incidencia (por 100.000 habitantes)
    - Áreas afectadas (departamentos únicos)
    - Letalidad (si hay datos de fallecidos)
    """

    # Base query para total de casos
    query_casos = """
    SELECT COUNT(*) as total_casos
    FROM evento e
    WHERE 1=1
    """

    params = {}

    # Aplicar filtros
    if grupo_id:
        query_casos += """
            AND e.id_tipo_eno IN (
                SELECT id FROM tipo_eno WHERE id_grupo_eno = :grupo_id
            )
        """
        params["grupo_id"] = grupo_id

    if evento_id:
        query_casos += " AND e.id_tipo_eno = :evento_id"
        params["evento_id"] = evento_id

    if fecha_desde:
        query_casos += " AND e.fecha_minima_evento >= :fecha_desde"
        params["fecha_desde"] = fecha_desde

    if fecha_hasta:
        query_casos += " AND e.fecha_minima_evento <= :fecha_hasta"
        params["fecha_hasta"] = fecha_hasta

    if clasificaciones:
        query_casos += " AND e.clasificacion_estrategia = ANY(:clasificaciones)"
        params["clasificaciones"] = clasificaciones

    # Ejecutar query de casos
    result_casos = await db.execute(text(query_casos), params)
    total_casos = result_casos.scalar() or 0

    # Query para áreas afectadas (departamentos únicos)
    query_areas = """
    SELECT COUNT(DISTINCT COALESCE(d.id_departamento_indec, 0)) as areas_afectadas
    FROM evento e
    LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
    LEFT JOIN localidad l ON est.id_localidad_establecimiento = l.id_localidad_indec
    LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
    WHERE 1=1
    """

    # Aplicar los mismos filtros
    if grupo_id:
        query_areas += """
            AND e.id_tipo_eno IN (
                SELECT id FROM tipo_eno WHERE id_grupo_eno = :grupo_id
            )
        """

    if evento_id:
        query_areas += " AND e.id_tipo_eno = :evento_id"

    if fecha_desde:
        query_areas += " AND e.fecha_minima_evento >= :fecha_desde"
        # params ya tiene las fechas convertidas

    if fecha_hasta:
        query_areas += " AND e.fecha_minima_evento <= :fecha_hasta"
        # params ya tiene las fechas convertidas

    if clasificaciones:
        query_areas += " AND e.clasificacion_estrategia = ANY(:clasificaciones)"
        # params ya tiene las clasificaciones

    result_areas = await db.execute(text(query_areas), params)
    areas_afectadas = result_areas.scalar() or 0

    # Para tasa de incidencia, necesitamos población (por ahora hardcodeado Chubut)
    poblacion_chubut = 618994  # Población estimada de Chubut 2024
    tasa_incidencia = round((total_casos / poblacion_chubut) * 100000, 2) if total_casos > 0 else 0

    # Letalidad (por ahora 0 porque no tenemos datos de fallecidos en el modelo actual)
    letalidad = 0  # TODO: Agregar cuando tengamos campo de fallecidos

    logger.info(f"Indicadores - Total casos: {total_casos}, Áreas: {areas_afectadas}, Tasa: {tasa_incidencia}")

    response = IndicadoresResponse(
        total_casos=total_casos,
        tasa_incidencia=tasa_incidencia,
        areas_afectadas=areas_afectadas,
        letalidad=letalidad,
        filtros_aplicados={
            "grupo_id": grupo_id,
            "evento_id": evento_id,
            "fecha_desde": fecha_desde.isoformat() if fecha_desde else None,
            "fecha_hasta": fecha_hasta.isoformat() if fecha_hasta else None,
            "clasificaciones": clasificaciones
        }
    )

    return SuccessResponse(data=response)
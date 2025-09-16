"""
Get indicadores endpoint
"""

from typing import Dict, Any, List
import logging
from datetime import datetime
from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_async_session
from app.core.security import RequireAnyRole
from app.domains.auth.models import User

logger = logging.getLogger(__name__)


async def get_indicadores(
    grupo_id: int = Query(None, description="ID del grupo seleccionado"),
    evento_id: int = Query(None, description="ID del evento seleccionado"),
    fecha_desde: str = Query(None, description="Fecha desde"),
    fecha_hasta: str = Query(None, description="Fecha hasta"),
    clasificaciones: List[str] = Query(None, description="Filtrar por clasificaciones estratégicas"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole())
) -> Dict[str, Any]:
    """
    Obtiene los indicadores de resumen para el dashboard

    Calcula:
    - Total de casos
    - Tasa de incidencia (por 100.000 habitantes)
    - Áreas afectadas (localidades/establecimientos únicos)
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
        params["fecha_desde"] = datetime.strptime(fecha_desde, "%Y-%m-%d").date()

    if fecha_hasta:
        query_casos += " AND e.fecha_minima_evento <= :fecha_hasta"
        params["fecha_hasta"] = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()

    if clasificaciones:
        query_casos += " AND e.clasificacion_estrategia = ANY(:clasificaciones)"
        params["clasificaciones"] = clasificaciones

    # Ejecutar query de casos
    result_casos = await db.execute(text(query_casos), params)
    total_casos = result_casos.scalar() or 0

    # Query para áreas afectadas (establecimientos únicos)
    query_areas = """
    SELECT COUNT(DISTINCT COALESCE(e.id_establecimiento_notificacion, 0)) as areas_afectadas
    FROM evento e
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

    return {
        "total_casos": total_casos,
        "tasa_incidencia": tasa_incidencia,
        "areas_afectadas": areas_afectadas,
        "letalidad": letalidad,
        "filtros_aplicados": {
            "grupo_id": grupo_id,
            "evento_id": evento_id,
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
            "clasificaciones": clasificaciones
        }
    }
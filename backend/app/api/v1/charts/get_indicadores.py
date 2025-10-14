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
    tipo_eno_ids: Optional[List[int]] = Query(None, description="IDs de los eventos a filtrar"),
    fecha_desde: Optional[date] = Query(None, description="Fecha desde (formato: YYYY-MM-DD)"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta (formato: YYYY-MM-DD)"),
    clasificaciones: Optional[List[str]] = Query(None, description="Filtrar por clasificaciones estratégicas"),
    provincia_id: Optional[int] = Query(None, description="Código INDEC de provincia (opcional, si no se envía muestra todas las provincias)"),
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
    # IMPORTANTE: Usar COUNT(DISTINCT e.id) para evitar duplicados por los JOINs
    query_casos = """
    SELECT COUNT(DISTINCT e.id) as total_casos
    FROM evento e
    LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
    LEFT JOIN localidad l ON est.id_localidad_indec = l.id_localidad_indec
    LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
    WHERE 1=1
    """

    params = {}

    # Filtro de provincia
    logger.info(f"🔍 Filtro provincia_id recibido: {provincia_id}")
    if provincia_id:
        query_casos += " AND d.id_provincia_indec = :provincia_id"
        params["provincia_id"] = provincia_id
        logger.info(f"✅ Aplicando filtro por provincia: {provincia_id}")
    else:
        logger.info(f"🌍 Sin filtro de provincia - buscando en TODAS las provincias")

    # Aplicar filtros
    if grupo_id:
        query_casos += """
            AND e.id_tipo_eno IN (
                SELECT id_tipo_eno FROM tipo_eno_grupo_eno WHERE id_grupo_eno = :grupo_id
            )
        """
        params["grupo_id"] = grupo_id

    if tipo_eno_ids and len(tipo_eno_ids) > 0:
        query_casos += " AND e.id_tipo_eno = ANY(:tipo_eno_ids)"
        params["tipo_eno_ids"] = tipo_eno_ids

    if fecha_desde:
        query_casos += " AND e.fecha_minima_evento >= :fecha_desde"
        params["fecha_desde"] = fecha_desde

    if fecha_hasta:
        query_casos += " AND e.fecha_minima_evento <= :fecha_hasta"
        params["fecha_hasta"] = fecha_hasta

    if clasificaciones:
        query_casos += " AND e.clasificacion_estrategia = ANY(:clasificaciones)"
        params["clasificaciones"] = clasificaciones

    # Log de filtros aplicados
    logger.info(f"📊 Filtros aplicados: grupo_id={params.get('grupo_id')}, tipo_eno_ids={params.get('tipo_eno_ids')}, "
                f"fecha_desde={params.get('fecha_desde')}, fecha_hasta={params.get('fecha_hasta')}, "
                f"clasificaciones={params.get('clasificaciones')}, provincia_id={params.get('provincia_id')}")

    # Ejecutar query de casos
    result_casos = await db.execute(text(query_casos), params)
    total_casos = result_casos.scalar() or 0

    logger.info(f"📈 Total casos encontrados: {total_casos}")

    # Query para áreas afectadas (departamentos únicos)
    query_areas = """
    SELECT COUNT(DISTINCT COALESCE(d.id_departamento_indec, 0)) as areas_afectadas
    FROM evento e
    LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
    LEFT JOIN localidad l ON est.id_localidad_indec = l.id_localidad_indec
    LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
    WHERE 1=1
    """

    # Filtro de provincia
    if provincia_id:
        query_areas += " AND d.id_provincia_indec = :provincia_id"

    # Aplicar los mismos filtros
    if grupo_id:
        query_areas += """
            AND e.id_tipo_eno IN (
                SELECT id_tipo_eno FROM tipo_eno_grupo_eno WHERE id_grupo_eno = :grupo_id
            )
        """

    if tipo_eno_ids and len(tipo_eno_ids) > 0:
        query_areas += " AND e.id_tipo_eno = ANY(:tipo_eno_ids)"

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

    logger.info(f"🗺️  Áreas afectadas: {areas_afectadas}")

    # Calcular población desde la base de datos
    if provincia_id:
        # Población de una provincia específica (suma de departamentos)
        query_poblacion = """
        SELECT COALESCE(SUM(poblacion), 0) as poblacion_total
        FROM departamento
        WHERE id_provincia_indec = :provincia_id
        """
        result_poblacion = await db.execute(text(query_poblacion), {"provincia_id": provincia_id})
        poblacion = result_poblacion.scalar() or 0
    else:
        # Población total del país (suma de todas las provincias/departamentos)
        query_poblacion = """
        SELECT COALESCE(SUM(poblacion), 0) as poblacion_total
        FROM departamento
        """
        result_poblacion = await db.execute(text(query_poblacion), {})
        poblacion = result_poblacion.scalar() or 0

    logger.info(f"👥 Población total calculada: {poblacion:,}")

    tasa_incidencia = round((total_casos / poblacion) * 100000, 2) if poblacion > 0 else 0

    # Letalidad (por ahora 0 porque no tenemos datos de fallecidos en el modelo actual)
    letalidad = 0  # TODO: Agregar cuando tengamos campo de fallecidos

    logger.info(f"📊 RESUMEN - Total casos: {total_casos}, Áreas: {areas_afectadas}, Población: {poblacion:,}, Tasa: {tasa_incidencia}/100k")

    response = IndicadoresResponse(
        total_casos=total_casos,
        tasa_incidencia=tasa_incidencia,
        areas_afectadas=areas_afectadas,
        letalidad=letalidad,
        filtros_aplicados={
            "grupo_id": grupo_id,
            "tipo_eno_ids": tipo_eno_ids,
            "fecha_desde": fecha_desde.isoformat() if fecha_desde else None,
            "fecha_hasta": fecha_hasta.isoformat() if fecha_hasta else None,
            "clasificaciones": clasificaciones,
            "provincia_id": provincia_id
        }
    )

    return SuccessResponse(data=response)
"""
Get indicadores endpoint
Retorna indicadores/métricas clave para los reportes
"""

import logging
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import Depends, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAuthOrSignedUrl
from app.domains.autenticacion.models import User

logger = logging.getLogger(__name__)


class IndicadoresData(BaseModel):
    """Indicadores clave para reportes"""
    total_casos: int = 0
    tasa_incidencia: float = 0.0
    areas_afectadas: int = 0
    letalidad: float = 0.0


async def get_indicadores(
    db: AsyncSession = Depends(get_async_session),
    current_user: User | None = RequireAuthOrSignedUrl,
    grupo_id: Optional[int] = Query(None),
    tipo_eno_ids: Optional[List[int]] = Query(None),
    fecha_desde: Optional[str] = Query(None),
    fecha_hasta: Optional[str] = Query(None),
    clasificaciones: Optional[List[str]] = Query(None),
    provincia_id: Optional[int] = Query(None),
) -> SuccessResponse[IndicadoresData]:
    """
    Obtiene indicadores clave basados en filtros

    Args:
        db: Sesión de base de datos
        current_user: Usuario autenticado o validado por signed URL
        grupo_id: Filtro por grupo de ENO
        tipo_eno_ids: Filtro por tipos de ENO
        fecha_desde: Fecha desde (formato ISO)
        fecha_hasta: Fecha hasta (formato ISO)
        clasificaciones: Filtro por clasificaciones
        provincia_id: Filtro por provincia (ej: 26 para Chubut)

    Returns:
        Indicadores calculados
    """
    try:
        params: Dict[str, Any] = {}
        where_clauses = []

        # Filtros de fechas
        if fecha_desde:
            where_clauses.append("e.fecha_minima_caso >= :fecha_desde")
            params["fecha_desde"] = date.fromisoformat(fecha_desde)

        if fecha_hasta:
            where_clauses.append("e.fecha_minima_caso <= :fecha_hasta")
            params["fecha_hasta"] = date.fromisoformat(fecha_hasta)

        # Filtro de provincia
        if provincia_id:
            where_clauses.append("d.id_provincia_indec = :provincia_id")
            params["provincia_id"] = provincia_id

        # Filtro de grupo
        if grupo_id:
            where_clauses.append("""
                e.id_enfermedad IN (
                    SELECT id_enfermedad FROM enfermedad_grupo WHERE id_grupo = :grupo_id
                )
            """)
            params["grupo_id"] = grupo_id

        # Filtro de tipos de ENO
        if tipo_eno_ids and len(tipo_eno_ids) > 0:
            where_clauses.append("e.id_enfermedad = ANY(:tipo_eno_ids)")
            params["tipo_eno_ids"] = tipo_eno_ids

        # Filtro de clasificaciones
        if clasificaciones:
            where_clauses.append("e.clasificacion_estrategia = ANY(:clasificaciones)")
            params["clasificaciones"] = clasificaciones

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Query 1: Total de casos y áreas afectadas
        query_casos = f"""
        SELECT
            COUNT(DISTINCT e.id) as total_casos,
            COUNT(DISTINCT d.id_departamento_indec) as areas_afectadas
        FROM caso_epidemiologico e
        LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
        LEFT JOIN localidad l ON est.id_localidad_indec = l.id_localidad_indec
        LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
        WHERE {where_sql}
        """

        result = await db.execute(text(query_casos), params)
        row = result.first()

        total_casos = row.total_casos if row else 0
        areas_afectadas = row.areas_afectadas if row else 0

        # Query 2: Población total
        if provincia_id:
            query_pob = "SELECT COALESCE(SUM(poblacion), 0) FROM departamento WHERE id_provincia_indec = :provincia_id"
            result_pob = await db.execute(text(query_pob), {"provincia_id": provincia_id})
        else:
            query_pob = "SELECT COALESCE(SUM(poblacion), 0) FROM departamento"
            result_pob = await db.execute(text(query_pob), {})

        poblacion = result_pob.scalar() or 0

        # Calcular tasa de incidencia (por 100,000 habitantes)
        tasa_incidencia = round((total_casos / poblacion) * 100000, 2) if poblacion > 0 else 0.0

        # TODO: Implementar cálculo de letalidad cuando se agregue la columna correspondiente
        # La tabla evento no tiene actualmente una columna para registrar fallecimientos
        letalidad = 0.0

        indicadores = IndicadoresData(
            total_casos=total_casos,
            tasa_incidencia=tasa_incidencia,
            areas_afectadas=areas_afectadas,
            letalidad=letalidad,
        )

        logger.info(f"📊 Indicadores calculados: {indicadores}")

        return SuccessResponse(data=indicadores)

    except Exception as e:
        logger.error(f"❌ Error calculando indicadores: {e}", exc_info=True)
        # Retornar indicadores vacíos en caso de error
        return SuccessResponse(
            data=IndicadoresData(
                total_casos=0,
                tasa_incidencia=0.0,
                areas_afectadas=0,
                letalidad=0.0,
            )
        )

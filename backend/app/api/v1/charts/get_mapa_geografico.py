"""
Get mapa geográfico endpoint - Datos de departamentos con estadísticas
"""

import logging
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAuthOrSignedUrl
from app.domains.autenticacion.models import User
from app.core.constants.geografia_chubut import (
    DEPARTAMENTOS_CHUBUT,
    POBLACION_DEPARTAMENTOS,
    get_zona_ugd,
    get_poblacion_departamento
)

logger = logging.getLogger(__name__)


class DepartamentoEstadistica(BaseModel):
    """Estadística de un departamento"""

    codigo_indec: int = Field(..., description="Código INDEC del departamento")
    nombre: str = Field(..., description="Nombre del departamento")
    zona_ugd: str = Field(..., description="Zona UGD del departamento")
    poblacion: int = Field(..., description="Población del departamento")
    casos: int = Field(..., description="Número de casos")
    tasa_incidencia: float = Field(..., description="Tasa de incidencia por 100.000 habitantes")


class MapaGeograficoResponse(BaseModel):
    """Response model para mapa geográfico"""

    departamentos: List[DepartamentoEstadistica] = Field(..., description="Lista de departamentos con estadísticas")
    total_casos: int = Field(..., description="Total de casos en toda la provincia")
    filtros_aplicados: Dict[str, Any] = Field(..., description="Filtros que se aplicaron")


async def get_mapa_geografico(
    grupo_id: Optional[int] = Query(None, description="ID del grupo seleccionado"),
    tipo_eno_ids: Optional[List[int]] = Query(None, description="IDs de los eventos a filtrar"),
    fecha_desde: Optional[date] = Query(None, description="Fecha desde (formato: YYYY-MM-DD)"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta (formato: YYYY-MM-DD)"),
    clasificaciones: Optional[List[str]] = Query(None, description="Filtrar por clasificaciones estratégicas"),
    provincia_id: Optional[int] = Query(None, description="Código INDEC de provincia (opcional, si no se envía muestra todas las provincias)"),
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = RequireAuthOrSignedUrl
) -> SuccessResponse[MapaGeograficoResponse]:
    """
    Obtiene estadísticas por departamento para visualización en mapa

    Incluye:
    - Casos por departamento
    - Tasa de incidencia
    - Información de zona UGD
    - Población
    """

    # Query para obtener casos por departamento
    query = """
    SELECT
        COALESCE(d.id_departamento_indec, 0) as codigo_indec,
        COALESCE(d.nombre, 'Sin datos') as nombre,
        COUNT(DISTINCT e.id) as casos
    FROM evento e
    LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
    LEFT JOIN localidad l ON est.id_localidad_indec = l.id_localidad_indec
    LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
    WHERE 1=1
    """

    params = {}

    # Filtro de provincia
    logger.info(f"🔍 Mapa - Filtro provincia_id recibido: {provincia_id}")
    if provincia_id:
        query += " AND d.id_provincia_indec = :provincia_id"
        params["provincia_id"] = provincia_id
        logger.info(f"✅ Mapa - Aplicando filtro por provincia: {provincia_id}")
    else:
        logger.info(f"🌍 Mapa - Sin filtro de provincia - mostrando TODAS las provincias")

    # Aplicar filtros
    if grupo_id:
        query += """
            AND e.id_tipo_eno IN (
                SELECT id_tipo_eno FROM tipo_eno_grupo_eno WHERE id_grupo_eno = :grupo_id
            )
        """
        params["grupo_id"] = grupo_id

    if tipo_eno_ids and len(tipo_eno_ids) > 0:
        query += " AND e.id_tipo_eno = ANY(:tipo_eno_ids)"
        params["tipo_eno_ids"] = tipo_eno_ids

    if fecha_desde:
        query += " AND e.fecha_minima_evento >= :fecha_desde"
        params["fecha_desde"] = fecha_desde

    if fecha_hasta:
        query += " AND e.fecha_minima_evento <= :fecha_hasta"
        params["fecha_hasta"] = fecha_hasta

    if clasificaciones:
        query += " AND e.clasificacion_estrategia = ANY(:clasificaciones)"
        params["clasificaciones"] = clasificaciones

    # Log de filtros aplicados
    logger.info(f"📊 Mapa - Filtros aplicados: grupo_id={params.get('grupo_id')}, tipo_eno_ids={params.get('tipo_eno_ids')}, "
                f"fecha_desde={params.get('fecha_desde')}, fecha_hasta={params.get('fecha_hasta')}, "
                f"clasificaciones={params.get('clasificaciones')}, provincia_id={params.get('provincia_id')}")

    query += " GROUP BY d.id_departamento_indec, d.nombre"

    # Ejecutar query
    result = await db.execute(text(query), params)
    rows = result.fetchall()

    logger.info(f"🗺️ Mapa - Filas encontradas en query: {len(rows)}")

    # Crear mapa de casos por departamento
    casos_por_departamento = {row.codigo_indec: row.casos for row in rows if row.codigo_indec}

    # Construir respuesta con todos los departamentos de Chubut
    departamentos_data = []
    total_casos = 0

    for codigo_indec in DEPARTAMENTOS_CHUBUT.keys():
        casos = casos_por_departamento.get(codigo_indec, 0)
        poblacion = get_poblacion_departamento(codigo_indec)
        tasa_incidencia = round((casos / poblacion) * 100000, 2) if poblacion > 0 else 0.0

        departamentos_data.append(DepartamentoEstadistica(
            codigo_indec=codigo_indec,
            nombre=DEPARTAMENTOS_CHUBUT[codigo_indec],
            zona_ugd=get_zona_ugd(codigo_indec),
            poblacion=poblacion,
            casos=casos,
            tasa_incidencia=tasa_incidencia
        ))

        total_casos += casos

    logger.info(f"📊 Mapa RESUMEN - Total departamentos: {len(departamentos_data)}, Total casos: {total_casos}")

    response = MapaGeograficoResponse(
        departamentos=departamentos_data,
        total_casos=total_casos,
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
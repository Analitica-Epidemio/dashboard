"""
Calculate changes for custom events - calcula cambios para eventos seleccionados manualmente
"""

import logging
from typing import Optional

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.analytics.period_utils import get_epi_week_dates
from app.api.v1.analytics.schemas import (
    CalculateChangesRequest,
    CalculateChangesResponse,
    CasoEpidemiologicoCambioConCategoria,
)
from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAuthOrSignedUrl
from app.domains.autenticacion.models import User

logger = logging.getLogger(__name__)


async def calculate_changes(
    request: CalculateChangesRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = RequireAuthOrSignedUrl,
) -> SuccessResponse[CalculateChangesResponse]:
    """
    Calcula cambios para eventos custom seleccionados por el usuario.

    La categoría (crecimiento/decrecimiento) se determina automáticamente
    basándose en el cambio porcentual.
    """

    if not request.tipo_eno_ids:
        return SuccessResponse(data=CalculateChangesResponse(eventos=[]))

    # Calcular fechas igual que en get_top_changes_by_group
    semana_inicio_actual = request.semana_actual - request.num_semanas + 1
    anio_inicio = request.anio_actual

    if semana_inicio_actual < 1:
        semana_inicio_actual += 52
        anio_inicio -= 1

    fecha_inicio_actual, _ = get_epi_week_dates(semana_inicio_actual, anio_inicio)
    _, fecha_fin_actual = get_epi_week_dates(request.semana_actual, request.anio_actual)

    # Período anterior
    semana_inicio_anterior = semana_inicio_actual - request.num_semanas
    anio_anterior = anio_inicio

    if semana_inicio_anterior < 1:
        semana_inicio_anterior += 52
        anio_anterior -= 1

    semana_fin_anterior = semana_inicio_anterior + request.num_semanas - 1

    fecha_inicio_anterior, _ = get_epi_week_dates(semana_inicio_anterior, anio_anterior)
    _, fecha_fin_anterior = get_epi_week_dates(semana_fin_anterior, anio_anterior)

    logger.info(
        f"Calculando cambios para {len(request.tipo_eno_ids)} eventos custom - "
        f"Actual: {fecha_inicio_actual} a {fecha_fin_actual}"
    )

    # Query optimizada para los eventos específicos
    query = text("""
        WITH casos_actual AS (
            SELECT
                te.id as tipo_eno_id,
                te.nombre as tipo_eno_nombre,
                ge.id as grupo_eno_id,
                ge.nombre as grupo_eno_nombre,
                COUNT(DISTINCT e.id) as casos
            FROM evento e
            INNER JOIN tipo_eno te ON e.id_enfermedad = te.id
            INNER JOIN tipo_eno_grupo_eno tege ON te.id = tege.id_enfermedad
            INNER JOIN grupo_eno ge ON tege.id_grupo = ge.id
            WHERE e.fecha_minima_caso >= :fecha_inicio_actual
                AND e.fecha_minima_caso <= :fecha_fin_actual
                AND te.id = ANY(:tipo_eno_ids)
            GROUP BY te.id, te.nombre, ge.id, ge.nombre
        ),
        casos_anterior AS (
            SELECT
                te.id as tipo_eno_id,
                COUNT(DISTINCT e.id) as casos
            FROM evento e
            INNER JOIN tipo_eno te ON e.id_enfermedad = te.id
            WHERE e.fecha_minima_caso >= :fecha_inicio_anterior
                AND e.fecha_minima_caso <= :fecha_fin_anterior
                AND te.id = ANY(:tipo_eno_ids)
            GROUP BY te.id
        )
        SELECT
            a.tipo_eno_id,
            a.tipo_eno_nombre,
            a.id_grupo,
            a.grupo_nombre,
            a.casos as casos_actuales,
            COALESCE(b.casos, 0) as casos_anteriores,
            (a.casos - COALESCE(b.casos, 0)) as diferencia_absoluta,
            CASE
                WHEN COALESCE(b.casos, 0) = 0 THEN
                    CASE WHEN a.casos > 0 THEN 999.99 ELSE 0 END
                ELSE ((a.casos - COALESCE(b.casos, 0))::float / b.casos * 100)
            END as diferencia_porcentual
        FROM casos_actual a
        LEFT JOIN casos_anterior b ON a.tipo_eno_id = b.tipo_eno_id
        ORDER BY a.tipo_eno_nombre
    """)

    result = await db.execute(
        query,
        {
            "fecha_inicio_actual": fecha_inicio_actual,
            "fecha_fin_actual": fecha_fin_actual,
            "fecha_inicio_anterior": fecha_inicio_anterior,
            "fecha_fin_anterior": fecha_fin_anterior,
            "tipo_eno_ids": request.tipo_eno_ids,
        },
    )
    rows = result.fetchall()

    # Procesar resultados
    eventos = []
    for row in rows:
        # Determinar categoría automáticamente
        diferencia_pct = float(row.diferencia_porcentual)
        if diferencia_pct > 0:
            categoria = "crecimiento"
        elif diferencia_pct < 0:
            categoria = "decrecimiento"
        else:
            categoria = "estable"

        eventos.append(
            CasoEpidemiologicoCambioConCategoria(
                tipo_eno_id=row.tipo_eno_id,
                tipo_eno_nombre=row.tipo_eno_nombre,
                grupo_eno_id=row.id_grupo,
                grupo_eno_nombre=row.grupo_nombre,
                casos_actuales=int(row.casos_actuales),
                casos_anteriores=int(row.casos_anteriores),
                diferencia_absoluta=int(row.diferencia_absoluta),
                diferencia_porcentual=round(diferencia_pct, 2),
                categoria=categoria,
            )
        )

    logger.info(f"Calculados cambios para {len(eventos)} eventos")

    return SuccessResponse(data=CalculateChangesResponse(eventos=eventos))

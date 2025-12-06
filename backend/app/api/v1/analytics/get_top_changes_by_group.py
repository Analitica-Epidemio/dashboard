"""
Get top changes by group - eventos con mayor crecimiento/decrecimiento por grupo
Optimizado con CTEs y window functions para evitar N+1 queries
"""

import logging
from typing import Optional

from fastapi import Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.analytics.period_utils import get_epi_week_dates
from app.api.v1.analytics.schemas import (
    CasoEpidemiologicoCambio,
    PeriodoAnalisis,
    TopChangesByGroupResponse,
)
from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAuthOrSignedUrl
from app.domains.autenticacion.models import User

logger = logging.getLogger(__name__)


async def get_top_changes_by_group(
    semana_actual: int = Query(
        ..., description="Semana epidemiológica actual", ge=1, le=53
    ),
    anio_actual: int = Query(..., description="Año epidemiológico actual"),
    num_semanas: int = Query(
        4, description="Número de semanas hacia atrás", ge=1, le=52
    ),
    limit: int = Query(10, description="Top N eventos por grupo", ge=1, le=50),
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = RequireAuthOrSignedUrl,
) -> SuccessResponse[TopChangesByGroupResponse]:
    """
    Endpoint optimizado para obtener top cambios por grupo epidemiológico.

    Calcula los N eventos con mayor crecimiento y decrecimiento para cada grupo,
    comparando el período actual vs el período anterior equivalente.

    Ejemplo:
    - semana_actual=40, anio_actual=2025, num_semanas=4
    - Período actual: semanas 37-40 del 2025
    - Período anterior: semanas 33-36 del 2025
    """

    # Calcular fechas del período actual
    # Retroceder num_semanas desde semana_actual
    semana_inicio_actual = semana_actual - num_semanas + 1
    anio_inicio = anio_actual

    # Manejar caso de semanas negativas (cruce de año)
    if semana_inicio_actual < 1:
        semana_inicio_actual += 52
        anio_inicio -= 1

    fecha_inicio_actual, _ = get_epi_week_dates(semana_inicio_actual, anio_inicio)
    _, fecha_fin_actual = get_epi_week_dates(semana_actual, anio_actual)

    # Calcular período anterior (mismo número de semanas)
    semana_inicio_anterior = semana_inicio_actual - num_semanas
    anio_anterior = anio_inicio

    if semana_inicio_anterior < 1:
        semana_inicio_anterior += 52
        anio_anterior -= 1

    semana_fin_anterior = semana_inicio_anterior + num_semanas - 1

    fecha_inicio_anterior, _ = get_epi_week_dates(semana_inicio_anterior, anio_anterior)
    _, fecha_fin_anterior = get_epi_week_dates(semana_fin_anterior, anio_anterior)

    logger.info(
        f"Calculando cambios - Actual: {fecha_inicio_actual} a {fecha_fin_actual}, "
        f"Anterior: {fecha_inicio_anterior} a {fecha_fin_anterior}"
    )

    # Query optimizada con CTEs para calcular todo en una sola pasada
    # IMPORTANTE: Un tipo_eno puede estar en múltiples grupos, usamos STRING_AGG para consolidar
    query = text("""
        WITH casos_actual AS (
            -- Casos por tipo_eno en período actual (sin duplicar por múltiples grupos)
            SELECT
                te.id as tipo_eno_id,
                te.nombre as tipo_eno_nombre,
                STRING_AGG(DISTINCT ge.nombre, ', ' ORDER BY ge.nombre) as grupos_nombres,
                COUNT(DISTINCT e.id) as casos
            FROM caso_epidemiologico e
            INNER JOIN enfermedad te ON e.id_enfermedad = te.id
            LEFT JOIN enfermedad_grupo tege ON te.id = tege.id_enfermedad
            LEFT JOIN grupo_de_enfermedades ge ON tege.id_grupo = ge.id
            WHERE e.fecha_minima_caso >= :fecha_inicio_actual
                AND e.fecha_minima_caso <= :fecha_fin_actual
            GROUP BY te.id, te.nombre
        ),
        casos_anterior AS (
            -- Casos por tipo_eno en período anterior
            SELECT
                te.id as tipo_eno_id,
                COUNT(DISTINCT e.id) as casos
            FROM caso_epidemiologico e
            INNER JOIN enfermedad te ON e.id_enfermedad = te.id
            WHERE e.fecha_minima_caso >= :fecha_inicio_anterior
                AND e.fecha_minima_caso <= :fecha_fin_anterior
            GROUP BY te.id
        ),
        cambios AS (
            -- Calcular cambios con CTEs anteriores
            SELECT
                a.tipo_eno_id,
                a.tipo_eno_nombre,
                a.grupos_nombres,
                a.casos as casos_actuales,
                COALESCE(b.casos, 0) as casos_anteriores,
                (a.casos - COALESCE(b.casos, 0)) as diferencia_absoluta,
                CASE
                    WHEN COALESCE(b.casos, 0) = 0 THEN
                        -- Si anterior es 0 y actual > 0, consideramos 100% de incremento
                        -- Si ambos son 0, es 0%
                        CASE WHEN a.casos > 0 THEN 100.0 ELSE 0 END
                    ELSE ((a.casos - COALESCE(b.casos, 0))::float / b.casos * 100)
                END as diferencia_porcentual
            FROM casos_actual a
            LEFT JOIN casos_anterior b ON a.tipo_eno_id = b.tipo_eno_id
        ),
        ranked_crecimiento AS (
            -- Ranking de crecimiento GLOBAL (sin particionar por grupo)
            -- Ordena por: 1) mayor incremento relativo, 2) mayor número de casos actuales
            SELECT
                *,
                ROW_NUMBER() OVER (
                    ORDER BY diferencia_porcentual DESC, casos_actuales DESC
                ) as rank
            FROM cambios
            WHERE diferencia_porcentual > 0
        ),
        ranked_decrecimiento AS (
            -- Ranking de decrecimiento GLOBAL (sin particionar por grupo)
            -- Ordena por: 1) mayor decrecimiento relativo, 2) mayor número de casos actuales
            SELECT
                *,
                ROW_NUMBER() OVER (
                    ORDER BY diferencia_porcentual ASC, casos_actuales DESC
                ) as rank
            FROM cambios
            WHERE diferencia_porcentual < 0
        )
        -- Combinar resultados con tipo de cambio
        SELECT
            tipo_eno_id,
            tipo_eno_nombre,
            grupos_nombres,
            casos_actuales,
            casos_anteriores,
            diferencia_absoluta,
            diferencia_porcentual,
            'crecimiento' as tipo_cambio
        FROM ranked_crecimiento
        WHERE rank <= :limit

        UNION ALL

        SELECT
            tipo_eno_id,
            tipo_eno_nombre,
            grupos_nombres,
            casos_actuales,
            casos_anteriores,
            diferencia_absoluta,
            diferencia_porcentual,
            'decrecimiento' as tipo_cambio
        FROM ranked_decrecimiento
        WHERE rank <= :limit

        ORDER BY tipo_cambio, diferencia_porcentual DESC
    """)

    # Ejecutar query
    result = await db.execute(
        query,
        {
            "fecha_inicio_actual": fecha_inicio_actual,
            "fecha_fin_actual": fecha_fin_actual,
            "fecha_inicio_anterior": fecha_inicio_anterior,
            "fecha_fin_anterior": fecha_fin_anterior,
            "limit": limit,
        },
    )
    rows = result.fetchall()

    # Procesar resultados SIN agrupar - solo dos listas globales
    top_crecimiento = []
    top_decrecimiento = []

    for row in rows:
        evento = CasoEpidemiologicoCambio(
            tipo_eno_id=row.tipo_eno_id,
            tipo_eno_nombre=row.tipo_eno_nombre,
            grupo_eno_id=0,  # No longer meaningful when evento can be in multiple groups
            grupo_eno_nombre=row.grupos_nombres
            or "Sin grupo",  # Concatenated group names
            casos_actuales=int(row.casos_actuales),
            casos_anteriores=int(row.casos_anteriores),
            diferencia_absoluta=int(row.diferencia_absoluta),
            diferencia_porcentual=round(float(row.diferencia_porcentual), 2),
        )

        if row.tipo_cambio == "crecimiento":
            top_crecimiento.append(evento)
        else:
            top_decrecimiento.append(evento)

    # Crear períodos
    periodo_actual = PeriodoAnalisis(
        semana_inicio=semana_inicio_actual,
        semana_fin=semana_actual,
        anio=anio_actual,
        fecha_inicio=fecha_inicio_actual,
        fecha_fin=fecha_fin_actual,
    )

    periodo_anterior = PeriodoAnalisis(
        semana_inicio=semana_inicio_anterior,
        semana_fin=semana_fin_anterior,
        anio=anio_anterior,
        fecha_inicio=fecha_inicio_anterior,
        fecha_fin=fecha_fin_anterior,
    )

    response = TopChangesByGroupResponse(
        periodo_actual=periodo_actual,
        periodo_anterior=periodo_anterior,
        top_crecimiento=top_crecimiento,
        top_decrecimiento=top_decrecimiento,
    )

    logger.info(
        f"Retornando {len(top_crecimiento)} eventos en crecimiento y {len(top_decrecimiento)} en decrecimiento"
    )

    return SuccessResponse(data=response)

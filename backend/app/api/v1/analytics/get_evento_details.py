"""
Get evento details - detalles completos de un evento para el dialog
Incluye resumen, trend semanal y metadatos
"""

import logging
from typing import Optional

from fastapi import Depends, Path, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.analytics.period_utils import get_epi_week_dates
from app.api.v1.analytics.schemas import (
    CasoEpidemiologicoDetailsResponse,
    GrupoDeEnfermedadesBasic,
    ResumenCasoEpidemiologico,
    EnfermedadBasic,
    TrendSemanal,
)
from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAuthOrSignedUrl
from app.domains.autenticacion.models import User
from app.domains.vigilancia_nominal.models.enfermedad import Enfermedad, EnfermedadGrupo

logger = logging.getLogger(__name__)


async def get_evento_details(
    tipo_eno_id: int = Path(..., description="ID del tipo de evento"),
    semana_actual: int = Query(..., description="Semana epidemiológica actual", ge=1, le=53),
    anio_actual: int = Query(..., description="Año epidemiológico actual"),
    num_semanas: int = Query(4, description="Número de semanas hacia atrás", ge=1, le=52),
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = RequireAuthOrSignedUrl
) -> SuccessResponse[CasoEpidemiologicoDetailsResponse]:
    """
    Obtiene detalles completos de un evento específico para mostrar en el dialog.

    Incluye:
    - Información del tipo de evento y su grupo
    - Resumen de cambio (casos actuales vs anteriores)
    - Serie temporal semanal con ambos períodos
    """

    # Calcular fechas de los períodos
    semana_inicio_actual = semana_actual - num_semanas + 1
    anio_inicio = anio_actual

    if semana_inicio_actual < 1:
        semana_inicio_actual += 52
        anio_inicio -= 1

    fecha_inicio_actual, _ = get_epi_week_dates(semana_inicio_actual, anio_inicio)
    _, fecha_fin_actual = get_epi_week_dates(semana_actual, anio_actual)

    # Período anterior
    semana_inicio_anterior = semana_inicio_actual - num_semanas
    anio_anterior = anio_inicio

    if semana_inicio_anterior < 1:
        semana_inicio_anterior += 52
        anio_anterior -= 1

    semana_fin_anterior = semana_inicio_anterior + num_semanas - 1

    fecha_inicio_anterior, _ = get_epi_week_dates(semana_inicio_anterior, anio_anterior)
    _, fecha_fin_anterior = get_epi_week_dates(semana_fin_anterior, anio_anterior)

    logger.info(f"Obteniendo detalles para evento {tipo_eno_id}")

    # 1. Obtener información del tipo de evento y su grupo
    query_tipo_eno = (
        select(Enfermedad)
        .where(Enfermedad.id == tipo_eno_id)
        .options(selectinload(Enfermedad.enfermedad_grupos).selectinload(EnfermedadGrupo.grupo))
    )
    result_tipo = await db.execute(query_tipo_eno)
    tipo_eno = result_tipo.scalar_one_or_none()

    if not tipo_eno:
        raise ValueError(f"Tipo de evento {tipo_eno_id} no encontrado")

    # Obtener el primer grupo (un evento puede tener múltiples grupos)
    grupo_eno = tipo_eno.enfermedad_grupos[0].grupo if tipo_eno.enfermedad_grupos else None

    if not grupo_eno:
        raise ValueError(f"CasoEpidemiologico {tipo_eno_id} no tiene grupo asociado")

    # 2. Calcular resumen de cambio
    query_resumen = text("""
        WITH casos_actual AS (
            SELECT COUNT(DISTINCT id) as casos
            FROM evento
            WHERE id_enfermedad = :tipo_eno_id
                AND fecha_minima_caso >= :fecha_inicio_actual
                AND fecha_minima_caso <= :fecha_fin_actual
        ),
        casos_anterior AS (
            SELECT COUNT(DISTINCT id) as casos
            FROM evento
            WHERE id_enfermedad = :tipo_eno_id
                AND fecha_minima_caso >= :fecha_inicio_anterior
                AND fecha_minima_caso <= :fecha_fin_anterior
        )
        SELECT
            a.casos as casos_actuales,
            b.casos as casos_anteriores,
            (a.casos - b.casos) as diferencia_absoluta,
            CASE
                WHEN b.casos = 0 THEN
                    CASE WHEN a.casos > 0 THEN 999.99 ELSE 0 END
                ELSE ((a.casos - b.casos)::float / b.casos * 100)
            END as diferencia_porcentual
        FROM casos_actual a, casos_anterior b
    """)

    result_resumen = await db.execute(query_resumen, {
        "tipo_eno_id": tipo_eno_id,
        "fecha_inicio_actual": fecha_inicio_actual,
        "fecha_fin_actual": fecha_fin_actual,
        "fecha_inicio_anterior": fecha_inicio_anterior,
        "fecha_fin_anterior": fecha_fin_anterior
    })
    row_resumen = result_resumen.fetchone()

    resumen = ResumenCasoEpidemiologico(
        casos_actuales=int(row_resumen.casos_actuales),
        casos_anteriores=int(row_resumen.casos_anteriores),
        diferencia_absoluta=int(row_resumen.diferencia_absoluta),
        diferencia_porcentual=round(float(row_resumen.diferencia_porcentual), 2)
    )

    # 3. Obtener serie temporal semanal para ambos períodos
    query_trend = text("""
        WITH semanas_actual AS (
            SELECT
                semana_epidemiologica,
                anio_epidemiologico,
                COUNT(DISTINCT id) as casos,
                'actual' as periodo
            FROM evento
            WHERE id_enfermedad = :tipo_eno_id
                AND fecha_minima_caso >= :fecha_inicio_actual
                AND fecha_minima_caso <= :fecha_fin_actual
            GROUP BY semana_epidemiologica, anio_epidemiologico
        ),
        semanas_anterior AS (
            SELECT
                semana_epidemiologica,
                anio_epidemiologico,
                COUNT(DISTINCT id) as casos,
                'anterior' as periodo
            FROM evento
            WHERE id_enfermedad = :tipo_eno_id
                AND fecha_minima_caso >= :fecha_inicio_anterior
                AND fecha_minima_caso <= :fecha_fin_anterior
            GROUP BY semana_epidemiologica, anio_epidemiologico
        )
        SELECT * FROM semanas_actual
        UNION ALL
        SELECT * FROM semanas_anterior
        ORDER BY periodo DESC, anio_epidemiologico, semana_epidemiologica
    """)

    result_trend = await db.execute(query_trend, {
        "tipo_eno_id": tipo_eno_id,
        "fecha_inicio_actual": fecha_inicio_actual,
        "fecha_fin_actual": fecha_fin_actual,
        "fecha_inicio_anterior": fecha_inicio_anterior,
        "fecha_fin_anterior": fecha_fin_anterior
    })
    rows_trend = result_trend.fetchall()

    trend_semanal = [
        TrendSemanal(
            semana=int(row.semana_epidemiologica),
            anio=int(row.anio_epidemiologico),
            casos=int(row.casos),
            periodo=row.periodo
        )
        for row in rows_trend
    ]

    # Construir response
    response = CasoEpidemiologicoDetailsResponse(
        tipo_eno=EnfermedadBasic(
            id=tipo_eno.id,
            nombre=tipo_eno.nombre,
            codigo=tipo_eno.slug
        ),
        grupo_eno=GrupoDeEnfermedadesBasic(
            id=grupo_eno.id,
            nombre=grupo_eno.nombre,
            descripcion=grupo_eno.descripcion
        ),
        resumen=resumen,
        trend_semanal=trend_semanal
    )

    logger.info(f"Detalles obtenidos para evento {tipo_eno_id}: {len(trend_semanal)} puntos en serie temporal")

    return SuccessResponse(data=response)

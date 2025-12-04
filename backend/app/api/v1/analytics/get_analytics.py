"""
Get analytics endpoint - comparación de métricas epidemiológicas entre períodos
"""

import logging
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.analytics.period_utils import (
    create_period_info,
    get_comparison_period,
    get_period_dates,
    get_period_description,
)
from app.api.v1.analytics.schemas import (
    AnalyticsResponse,
    CasosMetrics,
    CoberturaMetrics,
    ComparisonType,
    MetricValue,
    PerformanceMetrics,
    PeriodType,
)
from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAuthOrSignedUrl
from app.domains.autenticacion.models import User

logger = logging.getLogger(__name__)


def calculate_metric_value(valor_actual: float, valor_anterior: Optional[float]) -> MetricValue:
    """
    Calcula un MetricValue con la comparación entre valores.
    """
    if valor_anterior is None or valor_anterior == 0:
        return MetricValue(
            valor_actual=valor_actual,
            valor_anterior=valor_anterior,
            diferencia_absoluta=None,
            diferencia_porcentual=None,
            tendencia=None
        )

    dif_abs = valor_actual - valor_anterior
    dif_pct = (dif_abs / valor_anterior) * 100

    # Determinar tendencia
    if abs(dif_pct) < 5:  # Menos de 5% se considera estable
        tendencia = "stable"
    elif dif_pct > 0:
        tendencia = "up"
    else:
        tendencia = "down"

    return MetricValue(
        valor_actual=valor_actual,
        valor_anterior=valor_anterior,
        diferencia_absoluta=round(dif_abs, 2),
        diferencia_porcentual=round(dif_pct, 2),
        tendencia=tendencia
    )


async def query_casos_metrics(
    db: AsyncSession,
    fecha_desde: date,
    fecha_hasta: date,
    grupo_id: Optional[int],
    tipo_eno_ids: Optional[List[int]],
    clasificaciones: Optional[List[str]],
    provincia_id: Optional[int]
) -> Dict[str, Any]:
    """
    Consulta métricas de casos para un período específico.
    """
    params: Dict[str, Any] = {
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta
    }

    # Base query
    where_clauses = ["e.fecha_minima_evento >= :fecha_desde", "e.fecha_minima_evento <= :fecha_hasta"]

    if provincia_id:
        where_clauses.append("d.id_provincia_indec = :provincia_id")
        params["provincia_id"] = provincia_id

    if grupo_id:
        where_clauses.append("""
            e.id_tipo_eno IN (
                SELECT id_tipo_eno FROM tipo_eno_grupo_eno WHERE id_grupo_eno = :grupo_id
            )
        """)
        params["grupo_id"] = grupo_id

    if tipo_eno_ids and len(tipo_eno_ids) > 0:
        where_clauses.append("e.id_tipo_eno = ANY(:tipo_eno_ids)")
        params["tipo_eno_ids"] = tipo_eno_ids

    if clasificaciones:
        where_clauses.append("e.clasificacion_estrategia = ANY(:clasificaciones)")
        params["clasificaciones"] = clasificaciones

    where_sql = " AND ".join(where_clauses)

    # Query total de casos
    query_total = f"""
    SELECT COUNT(DISTINCT e.id) as total_casos
    FROM evento e
    LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
    LEFT JOIN localidad l ON est.id_localidad_indec = l.id_localidad_indec
    LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
    WHERE {where_sql}
    """

    result = await db.execute(text(query_total), params)
    total_casos = result.scalar() or 0

    # Query población
    if provincia_id:
        query_pob = "SELECT COALESCE(SUM(poblacion), 0) FROM departamento WHERE id_provincia_indec = :provincia_id"
        result_pob = await db.execute(text(query_pob), {"provincia_id": provincia_id})
    else:
        query_pob = "SELECT COALESCE(SUM(poblacion), 0) FROM departamento"
        result_pob = await db.execute(text(query_pob), {})

    poblacion = result_pob.scalar() or 0
    incidencia_100k = round((total_casos / poblacion) * 100000, 2) if poblacion > 0 else 0

    # Query casos por semana
    query_semanal = f"""
    SELECT
        EXTRACT(ISOYEAR FROM e.fecha_minima_evento)::int as anio_epi,
        EXTRACT(WEEK FROM e.fecha_minima_evento)::int as semana_epi,
        COUNT(DISTINCT e.id) as casos
    FROM evento e
    LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
    LEFT JOIN localidad l ON est.id_localidad_indec = l.id_localidad_indec
    LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
    WHERE {where_sql}
    GROUP BY anio_epi, semana_epi
    ORDER BY anio_epi, semana_epi
    """

    result_semanal = await db.execute(text(query_semanal), params)
    casos_por_semana = []
    total_semanas = 0

    for row in result_semanal:
        casos_por_semana.append({
            "anio_epi": row.anio_epi,
            "semana_epi": row.semana_epi,
            "casos": row.casos
        })
        total_semanas += 1

    promedio_semanal = round(total_casos / total_semanas, 2) if total_semanas > 0 else 0

    return {
        "total_casos": total_casos,
        "incidencia_100k": incidencia_100k,
        "promedio_semanal": promedio_semanal,
        "casos_por_semana": casos_por_semana
    }


async def query_cobertura_metrics(
    db: AsyncSession,
    fecha_desde: date,
    fecha_hasta: date,
    fecha_desde_comp: Optional[date],
    fecha_hasta_comp: Optional[date],
    grupo_id: Optional[int],
    tipo_eno_ids: Optional[List[int]],
    clasificaciones: Optional[List[str]],
    provincia_id: Optional[int]
) -> Dict[str, Any]:
    """
    Consulta métricas de cobertura geográfica.
    """
    params: Dict[str, Any] = {
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta
    }

    where_clauses = ["e.fecha_minima_evento >= :fecha_desde", "e.fecha_minima_evento <= :fecha_hasta"]

    if provincia_id:
        where_clauses.append("d.id_provincia_indec = :provincia_id")
        params["provincia_id"] = provincia_id

    if grupo_id:
        where_clauses.append("""
            e.id_tipo_eno IN (
                SELECT id_tipo_eno FROM tipo_eno_grupo_eno WHERE id_grupo_eno = :grupo_id
            )
        """)
        params["grupo_id"] = grupo_id

    if tipo_eno_ids and len(tipo_eno_ids) > 0:
        where_clauses.append("e.id_tipo_eno = ANY(:tipo_eno_ids)")
        params["tipo_eno_ids"] = tipo_eno_ids

    if clasificaciones:
        where_clauses.append("e.clasificacion_estrategia = ANY(:clasificaciones)")
        params["clasificaciones"] = clasificaciones

    where_sql = " AND ".join(where_clauses)

    # Áreas afectadas actual
    query_areas = f"""
    SELECT COUNT(DISTINCT d.id_departamento_indec) as areas_afectadas
    FROM evento e
    LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
    LEFT JOIN localidad l ON est.id_localidad_indec = l.id_localidad_indec
    LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
    WHERE {where_sql} AND d.id_departamento_indec IS NOT NULL
    """

    result = await db.execute(text(query_areas), params)
    areas_afectadas = result.scalar() or 0

    # Top departamentos
    query_top = f"""
    SELECT
        d.id_departamento_indec,
        d.nombre as departamento_nombre,
        COUNT(DISTINCT e.id) as casos
    FROM evento e
    LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
    LEFT JOIN localidad l ON est.id_localidad_indec = l.id_localidad_indec
    LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
    WHERE {where_sql} AND d.id_departamento_indec IS NOT NULL
    GROUP BY d.id_departamento_indec, d.nombre
    ORDER BY casos DESC
    LIMIT 10
    """

    result_top = await db.execute(text(query_top), params)
    top_departamentos = []
    for row in result_top:
        top_departamentos.append({
            "departamento_id": row.id_departamento_indec,
            "departamento_nombre": row.departamento_nombre,
            "casos": row.casos
        })

    # Nuevas áreas y áreas sin casos (si hay período de comparación)
    nuevas_areas = 0
    areas_sin_casos = 0

    if fecha_desde_comp and fecha_hasta_comp:
        # Departamentos en período actual
        query_deptos_actual = f"""
        SELECT DISTINCT d.id_departamento_indec
        FROM evento e
        LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
        LEFT JOIN localidad l ON est.id_localidad_indec = l.id_localidad_indec
        LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
        WHERE {where_sql} AND d.id_departamento_indec IS NOT NULL
        """

        result_actual = await db.execute(text(query_deptos_actual), params)
        deptos_actual = {row[0] for row in result_actual}

        # Departamentos en período anterior
        params_comp = params.copy()
        params_comp["fecha_desde"] = fecha_desde_comp
        params_comp["fecha_hasta"] = fecha_hasta_comp

        where_clauses_comp = [clause.replace(":fecha_desde", ":fecha_desde").replace(":fecha_hasta", ":fecha_hasta") for clause in where_clauses]
        where_sql_comp = " AND ".join(where_clauses_comp)

        query_deptos_comp = f"""
        SELECT DISTINCT d.id_departamento_indec
        FROM evento e
        LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
        LEFT JOIN localidad l ON est.id_localidad_indec = l.id_localidad_indec
        LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
        WHERE {where_sql_comp} AND d.id_departamento_indec IS NOT NULL
        """

        result_comp = await db.execute(text(query_deptos_comp), params_comp)
        deptos_comp = {row[0] for row in result_comp}

        nuevas_areas = len(deptos_actual - deptos_comp)
        areas_sin_casos = len(deptos_comp - deptos_actual)

    return {
        "areas_afectadas": areas_afectadas,
        "nuevas_areas": nuevas_areas,
        "areas_sin_casos": areas_sin_casos,
        "top_departamentos": top_departamentos
    }


async def query_performance_metrics(
    db: AsyncSession,
    fecha_desde: date,
    fecha_hasta: date,
    grupo_id: Optional[int],
    tipo_eno_ids: Optional[List[int]],
    clasificaciones: Optional[List[str]],
    provincia_id: Optional[int]
) -> Dict[str, Any]:
    """
    Consulta métricas de performance de clasificación.
    """
    params: Dict[str, Any] = {
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta
    }

    where_clauses = ["e.fecha_minima_evento >= :fecha_desde", "e.fecha_minima_evento <= :fecha_hasta"]

    if provincia_id:
        where_clauses.append("d.id_provincia_indec = :provincia_id")
        params["provincia_id"] = provincia_id

    if grupo_id:
        where_clauses.append("""
            e.id_tipo_eno IN (
                SELECT id_tipo_eno FROM tipo_eno_grupo_eno WHERE id_grupo_eno = :grupo_id
            )
        """)
        params["grupo_id"] = grupo_id

    if tipo_eno_ids and len(tipo_eno_ids) > 0:
        where_clauses.append("e.id_tipo_eno = ANY(:tipo_eno_ids)")
        params["tipo_eno_ids"] = tipo_eno_ids

    # Para performance, no filtramos por clasificación inicialmente
    where_sql = " AND ".join(where_clauses)

    # Tasa de confirmación
    query_tasas = f"""
    SELECT
        e.clasificacion_estrategia,
        COUNT(*) as total
    FROM evento e
    LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
    LEFT JOIN localidad l ON est.id_localidad_indec = l.id_localidad_indec
    LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
    WHERE {where_sql}
    GROUP BY e.clasificacion_estrategia
    """

    result = await db.execute(text(query_tasas), params)
    casos_por_clasificacion = {}
    total_casos = 0

    for row in result:
        if row.clasificacion_estrategia:
            casos_por_clasificacion[row.clasificacion_estrategia] = row.total
            total_casos += row.total

    confirmados = casos_por_clasificacion.get("CONFIRMADOS", 0)
    en_estudio = casos_por_clasificacion.get("EN_ESTUDIO", 0)

    tasa_confirmacion = round((confirmados / total_casos) * 100, 2) if total_casos > 0 else 0

    # Confianza promedio (si existe el campo)
    query_confianza = f"""
    SELECT AVG(e.confidence_score) as confianza_promedio
    FROM evento e
    LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
    LEFT JOIN localidad l ON est.id_localidad_indec = l.id_localidad_indec
    LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
    WHERE {where_sql} AND e.confidence_score IS NOT NULL
    """

    result_conf = await db.execute(text(query_confianza), params)
    confianza_promedio = result_conf.scalar() or 0
    confianza_promedio = round(float(confianza_promedio), 4) if confianza_promedio else 0

    return {
        "tasa_confirmacion": tasa_confirmacion,
        "tiempo_promedio_clasificacion": None,  # TODO: Implementar cuando tengamos fecha de clasificación
        "casos_en_estudio": en_estudio,
        "confianza_promedio": confianza_promedio
    }


async def get_analytics(
    period_type: PeriodType = Query(PeriodType.ULTIMAS_4_SEMANAS_EPI, description="Tipo de período predefinido"),
    fecha_desde: Optional[date] = Query(None, description="Fecha desde (solo si period_type=personalizado)"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta (solo si period_type=personalizado)"),
    comparison_type: ComparisonType = Query(ComparisonType.ROLLING, description="Tipo de comparación"),
    fecha_referencia: Optional[date] = Query(None, description="Fecha de referencia para 'viajar en el tiempo' y ver métricas históricas (ej: 2023-03-15)"),
    grupo_id: Optional[int] = Query(None, description="ID del grupo seleccionado"),
    tipo_eno_ids: Optional[List[int]] = Query(None, description="IDs de los eventos a filtrar"),
    clasificaciones: Optional[List[str]] = Query(None, description="Filtrar por clasificaciones estratégicas"),
    provincia_id: Optional[int] = Query(None, description="Código INDEC de provincia"),
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = RequireAuthOrSignedUrl
) -> SuccessResponse[AnalyticsResponse]:
    """
    Endpoint principal de analytics.

    Retorna métricas epidemiológicas comparadas entre dos períodos:
    - Casos confirmados y tendencias
    - Cobertura geográfica
    - Performance de clasificación
    """

    # Log parámetros recibidos
    logger.info("📊 Analytics - Parámetros recibidos:")
    logger.info(f"   - period_type: {period_type}")
    logger.info(f"   - fecha_referencia: {fecha_referencia or 'None (usando hoy)'}")
    logger.info(f"   - comparison_type: {comparison_type}")

    # Determinar fechas del período actual
    if period_type == PeriodType.PERSONALIZADO:
        if not fecha_desde or not fecha_hasta:
            raise ValueError("Para período personalizado debe especificar fecha_desde y fecha_hasta")
        periodo_desde = fecha_desde
        periodo_hasta = fecha_hasta
    else:
        periodo_desde, periodo_hasta = get_period_dates(
            period_type,
            fecha_referencia=fecha_referencia
        )

    # Crear PeriodInfo del período actual
    descripcion_actual = get_period_description(period_type, periodo_desde, periodo_hasta)
    periodo_actual = create_period_info(periodo_desde, periodo_hasta, descripcion_actual)

    # Determinar período de comparación
    if comparison_type == ComparisonType.ROLLING:
        comp_desde, comp_hasta = get_comparison_period(periodo_desde, periodo_hasta, "rolling")
        descripcion_comp = f"Período anterior ({comp_desde.strftime('%d/%m')} - {comp_hasta.strftime('%d/%m')})"
    elif comparison_type == ComparisonType.YEAR_OVER_YEAR:
        comp_desde, comp_hasta = get_comparison_period(periodo_desde, periodo_hasta, "year_over_year")
        descripcion_comp = f"Mismo período {comp_desde.year}"
    else:
        # BOTH - por ahora solo hacemos rolling, TODO: implementar ambos
        comp_desde, comp_hasta = get_comparison_period(periodo_desde, periodo_hasta, "rolling")
        descripcion_comp = f"Período anterior ({comp_desde.strftime('%d/%m')} - {comp_hasta.strftime('%d/%m')})"

    periodo_comparacion = create_period_info(comp_desde, comp_hasta, descripcion_comp)

    logger.info("📊 Analytics - Períodos calculados:")
    logger.info(f"   - Período actual: {periodo_desde} a {periodo_hasta}")
    logger.info(f"   - Período comparación: {comp_desde} a {comp_hasta}")

    # Consultar métricas para período actual
    casos_actual = await query_casos_metrics(
        db, periodo_desde, periodo_hasta,
        grupo_id, tipo_eno_ids, clasificaciones, provincia_id
    )

    # Consultar métricas para período de comparación
    casos_comp = await query_casos_metrics(
        db, comp_desde, comp_hasta,
        grupo_id, tipo_eno_ids, clasificaciones, provincia_id
    )

    # Construir CasosMetrics con comparación
    casos_metrics = CasosMetrics(
        total_casos=calculate_metric_value(casos_actual["total_casos"], casos_comp["total_casos"]),
        incidencia_100k=calculate_metric_value(casos_actual["incidencia_100k"], casos_comp["incidencia_100k"]),
        promedio_semanal=calculate_metric_value(casos_actual["promedio_semanal"], casos_comp["promedio_semanal"]),
        casos_por_semana=casos_actual["casos_por_semana"]
    )

    # Cobertura
    cobertura_actual = await query_cobertura_metrics(
        db, periodo_desde, periodo_hasta, comp_desde, comp_hasta,
        grupo_id, tipo_eno_ids, clasificaciones, provincia_id
    )

    cobertura_comp = await query_cobertura_metrics(
        db, comp_desde, comp_hasta, None, None,
        grupo_id, tipo_eno_ids, clasificaciones, provincia_id
    )

    cobertura_metrics = CoberturaMetrics(
        areas_afectadas=calculate_metric_value(cobertura_actual["areas_afectadas"], cobertura_comp["areas_afectadas"]),
        nuevas_areas=cobertura_actual["nuevas_areas"],
        areas_sin_casos=cobertura_actual["areas_sin_casos"],
        top_departamentos=cobertura_actual["top_departamentos"]
    )

    # Performance
    performance_actual = await query_performance_metrics(
        db, periodo_desde, periodo_hasta,
        grupo_id, tipo_eno_ids, clasificaciones, provincia_id
    )

    performance_comp = await query_performance_metrics(
        db, comp_desde, comp_hasta,
        grupo_id, tipo_eno_ids, clasificaciones, provincia_id
    )

    performance_metrics = PerformanceMetrics(
        tasa_confirmacion=calculate_metric_value(performance_actual["tasa_confirmacion"], performance_comp["tasa_confirmacion"]),
        tiempo_promedio_clasificacion=None,
        casos_en_estudio=calculate_metric_value(performance_actual["casos_en_estudio"], performance_comp["casos_en_estudio"]),
        confianza_promedio=calculate_metric_value(performance_actual["confianza_promedio"], performance_comp["confianza_promedio"])
    )

    response = AnalyticsResponse(
        periodo_actual=periodo_actual,
        periodo_comparacion=periodo_comparacion,
        tipo_comparacion=comparison_type,
        casos=casos_metrics,
        cobertura=cobertura_metrics,
        performance=performance_metrics,
        filtros_aplicados={
            "grupo_id": grupo_id,
            "tipo_eno_ids": tipo_eno_ids,
            "clasificaciones": clasificaciones,
            "provincia_id": provincia_id
        }
    )

    return SuccessResponse(data=response)

"""
API endpoints para charts dinámicos del dashboard
Simple y directo: un endpoint que devuelve los charts aplicables
"""
from typing import Dict, Any, List
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.core.database import get_async_session
from app.domains.charts.models import DashboardChart
from app.domains.charts.processors import ChartDataProcessor
from app.domains.charts.conditions import ChartConditionResolver

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/charts", tags=["Charts"])


@router.get("/dashboard")
async def get_dashboard_charts(
    grupo_id: int = Query(None, description="ID del grupo seleccionado"),
    evento_id: int = Query(None, description="ID del evento seleccionado"),
    fecha_desde: str = Query(None, description="Fecha desde"),
    fecha_hasta: str = Query(None, description="Fecha hasta"),
    clasificaciones: List[str] = Query(None, description="Filtrar por clasificaciones estratégicas"),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Obtiene los charts aplicables y sus datos según los filtros
    
    Simple: 
    1. Busca qué charts aplican según las condiciones
    2. Procesa los datos de cada chart
    3. Devuelve todo listo para renderizar
    """
    
    # Preparar filtros
    filtros = {
        "grupo_id": grupo_id,
        "evento_id": evento_id,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "clasificaciones": clasificaciones
    }
    
    # Obtener charts aplicables
    query = select(DashboardChart).where(DashboardChart.activo == True).order_by(DashboardChart.orden)
    result = await db.execute(query)
    all_charts = result.scalars().all()
    
    # Resolver condiciones usando códigos estables
    condition_resolver = ChartConditionResolver(db)
    charts_config = await condition_resolver.get_applicable_charts(filtros, all_charts)
    
    # Procesar cada chart aplicable
    processor = ChartDataProcessor(db)
    charts_data = []
    
    for chart_config in charts_config:
            
        # Procesar datos del chart
        try:
            logger.debug(f"Procesando chart {chart_config.codigo}")
            chart_data = await processor.process_chart(chart_config, filtros)
            
            charts_data.append({
                "codigo": chart_config.codigo,
                "nombre": chart_config.nombre,
                "descripcion": chart_config.descripcion,
                "tipo": chart_config.tipo_visualizacion,
                "data": chart_data,
                "config": chart_config.configuracion_chart or {}
            })
        except Exception as e:
            # Log error pero continuar con otros charts
            logger.error(f"Error procesando chart {chart_config.codigo}: {e}")
            continue
    
    return {
        "charts": charts_data,
        "total": len(charts_data),
        "filtros_aplicados": filtros
    }


@router.get("/indicadores")
async def get_indicadores(
    grupo_id: int = Query(None, description="ID del grupo seleccionado"),
    evento_id: int = Query(None, description="ID del evento seleccionado"),
    fecha_desde: str = Query(None, description="Fecha desde"),
    fecha_hasta: str = Query(None, description="Fecha hasta"),
    clasificaciones: List[str] = Query(None, description="Filtrar por clasificaciones estratégicas"),
    db: AsyncSession = Depends(get_async_session)
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


@router.get("/disponibles")
async def get_charts_disponibles(
    db: AsyncSession = Depends(get_async_session)
) -> List[Dict[str, Any]]:
    """
    Lista todos los charts disponibles sin procesar datos
    Útil para configuración y preview
    """
    query = select(DashboardChart).where(
        DashboardChart.activo == True
    ).order_by(DashboardChart.orden)
    
    result = await db.execute(query)
    charts = result.scalars().all()
    
    return [
        {
            "id": chart.id,
            "codigo": chart.codigo,
            "nombre": chart.nombre,
            "descripcion": chart.descripcion,
            "tipo_visualizacion": chart.tipo_visualizacion,
            "condiciones": chart.condiciones_display
        }
        for chart in charts
    ]



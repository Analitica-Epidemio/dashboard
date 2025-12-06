"""
Preview endpoints para secciones del boletín.
Endpoint genérico que genera resúmenes de datos basados en código de evento/grupo.
"""

import logging
from datetime import date
from typing import Literal, Optional

from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.analytics.period_utils import get_epi_week_dates
from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.domains.catalogos.agentes.models import (
    AgenteEtiologico,
)
from app.domains.vigilancia_nominal.models.enfermedad import GrupoDeEnfermedades, Enfermedad
from app.domains.vigilancia_nominal.models.caso import (    CasoEpidemiologico, CasoGrupoEnfermedad)

logger = logging.getLogger(__name__)


# ============================================================================
# SCHEMAS
# ============================================================================

class MetricItem(BaseModel):
    """Item de métrica para preview"""
    label: str
    value: str | int | float
    trend: Optional[Literal["up", "down", "stable"]] = None
    trend_value: Optional[float] = None
    alert: Optional[bool] = None


class CorredorPreview(BaseModel):
    """Preview de corredor endémico"""
    casos_acumulados: int
    zona_actual: Literal["exito", "seguridad", "alerta", "brote"]
    tendencia: Literal["up", "down", "stable"]
    porcentaje_cambio: Optional[float] = None


class SectionPreviewResponse(BaseModel):
    """Response de preview de sección"""
    evento_codigo: str
    evento_nombre: str
    evento_tipo: Literal["tipo_eno", "grupo_de_enfermedades"]
    summary: Optional[str] = None
    metrics: list[MetricItem] = Field(default_factory=list)
    corredor: Optional[CorredorPreview] = None
    periodo: Optional[dict] = None


class CasoEpidemiologicoDisponible(BaseModel):
    """CasoEpidemiologico disponible para selección en boletines"""
    id: int
    codigo: str
    nombre: str
    tipo: Literal["tipo_eno", "grupo_de_enfermedades"]


class AgenteDisponible(BaseModel):
    """Agente etiológico disponible para selección"""
    id: int
    codigo: str
    nombre: str
    nombre_corto: str
    categoria: str
    grupo: str


# ============================================================================
# HELPERS
# ============================================================================

def calculate_trend(current: int, previous: int) -> tuple[Literal["up", "down", "stable"], float]:
    """Calcula tendencia y porcentaje de cambio"""
    if previous == 0:
        if current > 0:
            return "up", 100.0
        return "stable", 0.0

    change = ((current - previous) / previous) * 100

    if change > 5:
        return "up", round(change, 1)
    elif change < -5:
        return "down", round(change, 1)
    else:
        return "stable", round(change, 1)


def calculate_zona(casos: int, media_historica: int) -> Literal["exito", "seguridad", "alerta", "brote"]:
    """
    Calcula la zona epidémica basada en desviación de la media histórica.
    Simplificación - en producción se usarían percentiles reales del corredor.
    """
    if media_historica == 0:
        return "seguridad" if casos == 0 else "alerta"

    ratio = casos / media_historica

    if ratio <= 0.75:
        return "exito"
    elif ratio <= 1.25:
        return "seguridad"
    elif ratio <= 1.75:
        return "alerta"
    else:
        return "brote"


async def get_evento_info(
    db: AsyncSession,
    codigo: str
) -> tuple[Optional[int], Optional[str], Literal["tipo_eno", "grupo_de_enfermedades"]]:
    """
    Busca un evento por código en Enfermedad o GrupoDeEnfermedades.
    Retorna (id, nombre, tipo).
    """
    # Primero buscar en Enfermedad
    stmt = select(Enfermedad.id, Enfermedad.nombre).where(Enfermedad.slug == codigo)
    result = await db.execute(stmt)
    tipo_eno = result.first()

    if tipo_eno:
        return tipo_eno.id, tipo_eno.nombre, "tipo_eno"

    # Si no está en Enfermedad, buscar en GrupoDeEnfermedades
    stmt = select(GrupoDeEnfermedades.id, GrupoDeEnfermedades.nombre).where(GrupoDeEnfermedades.slug == codigo)
    result = await db.execute(stmt)
    grupo_eno = result.first()

    if grupo_eno:
        return grupo_eno.id, grupo_eno.nombre, "grupo_de_enfermedades"

    return None, None, "tipo_eno"


async def count_casos_periodo(
    db: AsyncSession,
    evento_id: int,
    evento_tipo: Literal["tipo_eno", "grupo_de_enfermedades"],
    fecha_inicio: date,
    fecha_fin: date,
    solo_confirmados: bool = False,
) -> int:
    """Cuenta casos en un período dado"""
    if evento_tipo == "tipo_eno":
        stmt = select(func.count(CasoEpidemiologico.id)).where(
            CasoEpidemiologico.id_enfermedad == evento_id,
            CasoEpidemiologico.fecha_minima_caso >= fecha_inicio,
            CasoEpidemiologico.fecha_minima_caso <= fecha_fin,
        )
    else:
        # Para grupo, necesitamos JOIN con la tabla intermedia
        stmt = (
            select(func.count(CasoEpidemiologico.id))
            .join(CasoGrupoEnfermedad, CasoEpidemiologico.id == CasoGrupoEnfermedad.id_evento)
            .where(
                CasoGrupoEnfermedad.id_grupo == evento_id,
                CasoEpidemiologico.fecha_minima_caso >= fecha_inicio,
                CasoEpidemiologico.fecha_minima_caso <= fecha_fin,
            )
        )

    if solo_confirmados:
        stmt = stmt.where(CasoEpidemiologico.clasificacion_manual == "Confirmado")

    result = await db.execute(stmt)
    return result.scalar() or 0


async def get_casos_por_clasificacion(
    db: AsyncSession,
    evento_id: int,
    evento_tipo: Literal["tipo_eno", "grupo_de_enfermedades"],
    fecha_inicio: date,
    fecha_fin: date,
) -> list[tuple[str, int]]:
    """Obtiene casos agrupados por clasificación"""
    if evento_tipo == "tipo_eno":
        stmt = (
            select(
                CasoEpidemiologico.clasificacion_manual,
                func.count(CasoEpidemiologico.id).label("casos")
            )
            .where(
                CasoEpidemiologico.id_enfermedad == evento_id,
                CasoEpidemiologico.fecha_minima_caso >= fecha_inicio,
                CasoEpidemiologico.fecha_minima_caso <= fecha_fin,
            )
            .group_by(CasoEpidemiologico.clasificacion_manual)
            .order_by(func.count(CasoEpidemiologico.id).desc())
        )
    else:
        stmt = (
            select(
                CasoEpidemiologico.clasificacion_manual,
                func.count(CasoEpidemiologico.id).label("casos")
            )
            .join(CasoGrupoEnfermedad, CasoEpidemiologico.id == CasoGrupoEnfermedad.id_evento)
            .where(
                CasoGrupoEnfermedad.id_grupo == evento_id,
                CasoEpidemiologico.fecha_minima_caso >= fecha_inicio,
                CasoEpidemiologico.fecha_minima_caso <= fecha_fin,
            )
            .group_by(CasoEpidemiologico.clasificacion_manual)
            .order_by(func.count(CasoEpidemiologico.id).desc())
        )

    result = await db.execute(stmt)
    return [(row.clasificacion_manual or "Sin clasificar", row.casos) for row in result.all()]


# ============================================================================
# GENERIC PREVIEW ENDPOINT
# ============================================================================

async def get_evento_preview(
    codigo: str = Query(..., description="Código del Enfermedad o GrupoDeEnfermedades"),
    semana: int = Query(..., ge=1, le=53, description="Semana epidemiológica"),
    anio: int = Query(..., ge=2020, le=2030, description="Año"),
    num_semanas: int = Query(4, ge=1, le=52, description="Semanas a analizar"),
    db: AsyncSession = Depends(get_async_session),
) -> SuccessResponse[SectionPreviewResponse]:
    """
    Preview genérico de datos para cualquier evento epidemiológico.

    Recibe el código del Enfermedad o GrupoDeEnfermedades y genera un resumen con:
    - Total de casos en el período
    - Comparación con período anterior
    - Distribución por clasificación
    - Zona epidémica aproximada
    """
    try:
        # Buscar el evento por código
        evento_id, evento_nombre, evento_tipo = await get_evento_info(db, codigo)

        if evento_id is None:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró evento con código: {codigo}"
            )

        # Calcular fechas del período actual
        semana_inicio = max(1, semana - num_semanas + 1)
        fecha_inicio, _ = get_epi_week_dates(semana_inicio, anio)
        _, fecha_fin = get_epi_week_dates(semana, anio)

        # Calcular fechas del período anterior (para comparación)
        semana_anterior_fin = semana_inicio - 1
        if semana_anterior_fin < 1:
            anio_anterior = anio - 1
            semana_anterior_fin = 52
            semana_anterior_inicio = max(1, semana_anterior_fin - num_semanas + 1)
        else:
            anio_anterior = anio
            semana_anterior_inicio = max(1, semana_anterior_fin - num_semanas + 1)

        fecha_inicio_ant, _ = get_epi_week_dates(semana_anterior_inicio, anio_anterior)
        _, fecha_fin_ant = get_epi_week_dates(semana_anterior_fin, anio_anterior)

        # Contar casos período actual
        casos_actual = await count_casos_periodo(
            db, evento_id, evento_tipo, fecha_inicio, fecha_fin
        )
        casos_confirmados = await count_casos_periodo(
            db, evento_id, evento_tipo, fecha_inicio, fecha_fin, solo_confirmados=True
        )

        # Contar casos período anterior
        casos_anterior = await count_casos_periodo(
            db, evento_id, evento_tipo, fecha_inicio_ant, fecha_fin_ant
        )

        # Calcular tendencia
        trend, trend_value = calculate_trend(casos_actual, casos_anterior)

        # Obtener distribución por clasificación
        clasificaciones = await get_casos_por_clasificacion(
            db, evento_id, evento_tipo, fecha_inicio, fecha_fin
        )

        # Construir métricas
        metrics = [
            MetricItem(
                label="Total casos",
                value=casos_actual,
                trend=trend,
                trend_value=trend_value,
            ),
            MetricItem(
                label="Confirmados",
                value=casos_confirmados,
            ),
        ]

        # Agregar top clasificaciones como métricas
        for clasif, count in clasificaciones[:3]:
            if clasif != "Confirmado":  # Ya lo mostramos arriba
                metrics.append(MetricItem(label=clasif, value=count))

        # Calcular zona epidémica (simplificado)
        zona = calculate_zona(casos_actual, casos_anterior if casos_anterior > 0 else casos_actual)

        # Construir corredor preview
        corredor = CorredorPreview(
            casos_acumulados=casos_actual,
            zona_actual=zona,
            tendencia=trend,
            porcentaje_cambio=trend_value,
        )

        # Construir summary
        if casos_actual == 0:
            summary = "Sin casos registrados en el período"
        else:
            trend_text = {
                "up": f"↑ {abs(trend_value):.1f}%",
                "down": f"↓ {abs(trend_value):.1f}%",
                "stable": "estable",
            }[trend]
            summary = f"{casos_actual} casos totales ({casos_confirmados} confirmados) - {trend_text} vs período anterior"

        return SuccessResponse(
            data=SectionPreviewResponse(
                evento_codigo=codigo,
                evento_nombre=evento_nombre,
                evento_tipo=evento_tipo,
                summary=summary,
                metrics=metrics,
                corredor=corredor,
                periodo={
                    "semana_inicio": semana_inicio,
                    "semana_fin": semana,
                    "anio": anio,
                    "fecha_inicio": fecha_inicio.isoformat(),
                    "fecha_fin": fecha_fin.isoformat(),
                },
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en preview evento {codigo}: {e}", exc_info=True)
        return SuccessResponse(
            data=SectionPreviewResponse(
                evento_codigo=codigo,
                evento_nombre=codigo,
                evento_tipo="tipo_eno",
                summary="Error al cargar datos",
                metrics=[],
            )
        )


async def list_available_eventos(
    db: AsyncSession = Depends(get_async_session),
) -> SuccessResponse[list[CasoEpidemiologicoDisponible]]:
    """
    Lista todos los eventos disponibles (Enfermedad y GrupoDeEnfermedades) para selección.
    Útil para el frontend al construir el selector de secciones.
    """
    try:
        eventos = []

        # Obtener Enfermedad con código
        stmt = select(Enfermedad.id, Enfermedad.slug, Enfermedad.nombre).where(
            Enfermedad.slug.isnot(None)
        ).order_by(Enfermedad.nombre)
        result = await db.execute(stmt)

        for row in result.all():
            eventos.append(CasoEpidemiologicoDisponible(
                id=row.id,
                codigo=row.slug,
                nombre=row.nombre,
                tipo="tipo_eno",
            ))

        # Obtener GrupoDeEnfermedades con código
        stmt = select(GrupoDeEnfermedades.id, GrupoDeEnfermedades.slug, GrupoDeEnfermedades.nombre).where(
            GrupoDeEnfermedades.slug.isnot(None)
        ).order_by(GrupoDeEnfermedades.nombre)
        result = await db.execute(stmt)

        for row in result.all():
            eventos.append(CasoEpidemiologicoDisponible(
                id=row.id,
                codigo=row.slug,
                nombre=row.nombre,
                tipo="grupo_de_enfermedades",
            ))

        return SuccessResponse(data=eventos)

    except Exception as e:
        logger.error(f"Error listando eventos: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error al listar eventos")


async def list_available_agentes(
    db: AsyncSession = Depends(get_async_session),
) -> SuccessResponse[list[AgenteDisponible]]:
    """
    Lista todos los agentes etiológicos disponibles para selección.
    Útil para el frontend al construir selectores de agentes en bloques dinámicos.
    """
    try:
        agentes = []

        # Obtener agentes activos
        stmt = select(
            AgenteEtiologico.id,
            AgenteEtiologico.slug,
            AgenteEtiologico.nombre,
            AgenteEtiologico.nombre_corto,
            AgenteEtiologico.categoria,
            AgenteEtiologico.grupo,
        ).where(
            AgenteEtiologico.activo.is_(True)
        ).order_by(AgenteEtiologico.grupo, AgenteEtiologico.nombre)

        result = await db.execute(stmt)

        for row in result.all():
            agentes.append(AgenteDisponible(
                id=row.id,
                codigo=row.slug,
                nombre=row.nombre,
                nombre_corto=row.nombre_corto,
                categoria=row.categoria,
                grupo=row.grupo,
            ))

        return SuccessResponse(data=agentes)

    except Exception as e:
        logger.error(f"Error listando agentes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error al listar agentes")


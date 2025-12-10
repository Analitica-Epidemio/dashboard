"""
Endpoint para exponer configuración de secciones y bloques al frontend.

Permite al frontend entender exactamente qué datos se van a generar
para cada sección y bloque, incluyendo los rangos temporales.
"""

import re
from datetime import date
from typing import Optional

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import col, select

from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.domains.boletines.models import BoletinBloque, BoletinSeccion

from .schemas import (
    BloqueConfigResponse,
    RangoTemporalInfo,
    SeccionConfigResponse,
    SeccionesConfigResponse,
)


def _interpretar_rango_temporal(
    rango_temporal: Optional[str],
    semana_ref: int,
    anio_ref: int,
    tipo_bloque: str,
) -> RangoTemporalInfo:
    """
    Interpreta el código de rango temporal y genera descripción legible.

    Args:
        rango_temporal: Código del rango (anio_completo, ultimas_6_semanas, etc)
        semana_ref: Semana epidemiológica de referencia
        anio_ref: Año de referencia
        tipo_bloque: Tipo del bloque (para inferir default)

    Returns:
        RangoTemporalInfo con descripción y ejemplo concreto
    """
    # Default para corredor endémico
    if not rango_temporal and tipo_bloque == "corredor_endemico":
        anios_historicos = [2018, 2019, 2022, 2023, 2024]
        return RangoTemporalInfo(
            codigo="corredor_endemico_default",
            descripcion="Años históricos (excluyendo pandemia) + año actual",
            ejemplo=f"Años {', '.join(map(str, anios_historicos))} y {anio_ref}, SE 1 a {semana_ref}",
        )

    # Default: últimas 4 semanas
    if not rango_temporal:
        semana_desde = max(1, semana_ref - 3)
        return RangoTemporalInfo(
            codigo="ultimas_4_semanas",
            descripcion="Últimas 4 semanas epidemiológicas",
            ejemplo=f"SE {semana_desde} a SE {semana_ref} de {anio_ref}",
        )

    # Año completo
    if rango_temporal == "anio_completo":
        return RangoTemporalInfo(
            codigo="anio_completo",
            descripcion="Año completo hasta la semana de referencia",
            ejemplo=f"SE 1 a SE {semana_ref} de {anio_ref}",
        )

    # Últimas N semanas
    match = re.match(r"ultimas_(\d+)_semanas", rango_temporal)
    if match:
        n_semanas = int(match.group(1))
        semana_desde = max(1, semana_ref - n_semanas + 1)
        return RangoTemporalInfo(
            codigo=rango_temporal,
            descripcion=f"Últimas {n_semanas} semanas epidemiológicas",
            ejemplo=f"SE {semana_desde} a SE {semana_ref} de {anio_ref}",
        )

    # Histórico desde año YYYY
    match = re.match(r"historico_desde_(\d{4})", rango_temporal)
    if match:
        anio_desde = int(match.group(1))
        return RangoTemporalInfo(
            codigo=rango_temporal,
            descripcion=f"Serie histórica desde {anio_desde}",
            ejemplo=f"Años {anio_desde} a {anio_ref}, SE 1 a {semana_ref} del año actual",
        )

    # Años específicos
    match = re.match(r"anios:(.+)", rango_temporal)
    if match:
        anios_str = match.group(1)
        return RangoTemporalInfo(
            codigo=rango_temporal,
            descripcion="Años específicos seleccionados",
            ejemplo=f"Años {anios_str}, SE 1 a {semana_ref} del año actual",
        )

    # Default fallback
    return RangoTemporalInfo(
        codigo=rango_temporal or "default",
        descripcion="Rango temporal por defecto",
        ejemplo=f"SE 1 a SE {semana_ref} de {anio_ref}",
    )


def _bloque_to_response(
    bloque: BoletinBloque,
    semana_ref: int,
    anio_ref: int,
) -> BloqueConfigResponse:
    """Convierte un bloque a su respuesta con info de rango temporal."""
    config_visual = bloque.config_visual or {}
    rango_temporal = config_visual.get("rango_temporal")

    return BloqueConfigResponse(
        id=bloque.id,  # type: ignore[arg-type]
        slug=bloque.slug,
        titulo_template=bloque.titulo_template,
        tipo_bloque=bloque.tipo_bloque.value,
        tipo_visualizacion=bloque.tipo_visualizacion.value,
        metrica_codigo=bloque.metrica_codigo,
        dimensiones=bloque.dimensiones,
        rango_temporal=_interpretar_rango_temporal(
            rango_temporal, semana_ref, anio_ref, bloque.tipo_bloque.value
        ),
        descripcion=bloque.descripcion,
        orden=bloque.orden,
    )


async def get_secciones_config(
    semana: Optional[int] = Query(
        default=None,
        description="Semana epidemiológica de referencia (default: semana actual)",
        ge=1,
        le=53,
    ),
    anio: Optional[int] = Query(
        default=None,
        description="Año de referencia (default: año actual)",
        ge=2014,
        le=2100,
    ),
    session: AsyncSession = Depends(get_async_session),
) -> SuccessResponse[SeccionesConfigResponse]:
    """
    Obtiene la configuración de todas las secciones y bloques activos.

    Retorna información detallada sobre qué datos se incluirán en cada bloque,
    con ejemplos concretos basados en la semana de referencia seleccionada.
    """
    # Defaults: semana y año actual
    hoy = date.today()
    if anio is None:
        anio = hoy.year
    if semana is None:
        # Calcular semana epidemiológica aproximada
        semana = min(hoy.isocalendar()[1], 52)

    # Obtener secciones activas con sus bloques (eager loading)
    stmt = (
        select(BoletinSeccion)
        .options(selectinload(BoletinSeccion.bloques))  # type: ignore[arg-type]
        .where(col(BoletinSeccion.activo).is_(True))
        .order_by(col(BoletinSeccion.orden))
    )
    result = await session.execute(stmt)
    secciones = result.scalars().all()

    # Construir respuesta
    secciones_response = []
    total_bloques = 0

    for seccion in secciones:
        bloques_activos = [b for b in seccion.bloques if b.activo]
        total_bloques += len(bloques_activos)

        secciones_response.append(
            SeccionConfigResponse(
                id=seccion.id,  # type: ignore[arg-type]
                slug=seccion.slug,
                titulo=seccion.titulo,
                descripcion=seccion.descripcion,
                orden=seccion.orden,
                bloques=[_bloque_to_response(b, semana, anio) for b in bloques_activos],
            )
        )

    return SuccessResponse(
        data=SeccionesConfigResponse(
            secciones=secciones_response,
            semana_referencia=semana,
            anio_referencia=anio,
            total_bloques=total_bloques,
        )
    )

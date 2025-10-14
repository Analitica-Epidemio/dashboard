"""
Script para analizar fechas de eventos de Dengue en Chubut.
Investiga por qué hay 357 eventos sin filtro de fecha vs 102 con filtro.
"""

import asyncio
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.domains.eventos_epidemiologicos.eventos.models import Evento, TipoEno, TipoEnoGrupoEno
from app.domains.sujetos_epidemiologicos.ciudadanos_models import Ciudadano, CiudadanoDomicilio
from app.domains.territorio.geografia_models import Departamento, Localidad, Provincia


async def analyze_dengue_dates():
    """Analiza las fechas de eventos de Dengue en Chubut."""

    async for db in get_async_session():
        try:
            # Query base: Dengue (tipo_eno_id=1, grupo_eno_id=6) en Chubut (provincia_id=26)
            base_query = (
                select(Evento)
                .outerjoin(TipoEno, Evento.id_tipo_eno == TipoEno.id)
                .outerjoin(TipoEnoGrupoEno, TipoEno.id == TipoEnoGrupoEno.id_tipo_eno)
                .outerjoin(Ciudadano, Evento.codigo_ciudadano == Ciudadano.codigo_ciudadano)
                .outerjoin(CiudadanoDomicilio, Ciudadano.codigo_ciudadano == CiudadanoDomicilio.codigo_ciudadano)
                .outerjoin(Localidad, CiudadanoDomicilio.id_localidad_indec == Localidad.id_localidad_indec)
                .outerjoin(Departamento, Localidad.id_departamento_indec == Departamento.id_departamento_indec)
                .outerjoin(Provincia, Departamento.id_provincia_indec == Provincia.id_provincia_indec)
                .where(
                    and_(
                        Evento.id_tipo_eno == 1,  # Dengue
                        TipoEnoGrupoEno.id_grupo_eno == 6,  # Grupo Dengue
                        Provincia.id_provincia_indec == 26,  # Chubut
                    )
                )
            )

            # 1. Total de eventos (con DISTINCT para evitar duplicados)
            total_query = select(func.count(func.distinct(Evento.id))).select_from(base_query.subquery())
            total_result = await db.execute(total_query)
            total = total_result.scalar()

            print(f"\n{'='*60}")
            print(f"📊 ANÁLISIS DE FECHAS - DENGUE EN CHUBUT")
            print(f"{'='*60}\n")
            print(f"Total eventos (DISTINCT): {total}")

            # 2. Eventos SIN fecha_minima_evento
            sin_fecha_query = (
                select(func.count(func.distinct(Evento.id)))
                .select_from(
                    base_query.where(Evento.fecha_minima_evento.is_(None)).subquery()
                )
            )
            sin_fecha_result = await db.execute(sin_fecha_query)
            sin_fecha = sin_fecha_result.scalar()

            print(f"\n🚫 Eventos SIN fecha_minima_evento: {sin_fecha}")

            # 3. Rango de fechas de los eventos CON fecha
            fecha_range_query = (
                select(
                    func.min(Evento.fecha_minima_evento).label("fecha_min"),
                    func.max(Evento.fecha_minima_evento).label("fecha_max"),
                )
                .select_from(
                    base_query.where(Evento.fecha_minima_evento.isnot(None)).subquery()
                )
            )
            fecha_range_result = await db.execute(fecha_range_query)
            fecha_range = fecha_range_result.one()

            print(f"\n📅 Rango de fechas:")
            print(f"   Fecha mínima: {fecha_range.fecha_min}")
            print(f"   Fecha máxima: {fecha_range.fecha_max}")

            # 4. Eventos dentro del rango del dashboard (1995-11-26 a 2026-01-03)
            from datetime import date
            fecha_desde = date(1995, 11, 26)
            fecha_hasta = date(2026, 1, 3)

            en_rango_query = (
                select(func.count(func.distinct(Evento.id)))
                .select_from(
                    base_query.where(
                        and_(
                            Evento.fecha_minima_evento >= fecha_desde,
                            Evento.fecha_minima_evento <= fecha_hasta,
                        )
                    ).subquery()
                )
            )
            en_rango_result = await db.execute(en_rango_query)
            en_rango = en_rango_result.scalar()

            print(f"\n✅ Eventos en rango {fecha_desde} - {fecha_hasta}: {en_rango}")

            # 5. Eventos ANTES de 1995-11-26
            antes_query = (
                select(func.count(func.distinct(Evento.id)))
                .select_from(
                    base_query.where(Evento.fecha_minima_evento < fecha_desde).subquery()
                )
            )
            antes_result = await db.execute(antes_query)
            antes = antes_result.scalar()

            print(f"⏪ Eventos ANTES de {fecha_desde}: {antes}")

            # 6. Eventos DESPUÉS de 2026-01-03
            despues_query = (
                select(func.count(func.distinct(Evento.id)))
                .select_from(
                    base_query.where(Evento.fecha_minima_evento > fecha_hasta).subquery()
                )
            )
            despues_result = await db.execute(despues_query)
            despues = despues_result.scalar()

            print(f"⏩ Eventos DESPUÉS de {fecha_hasta}: {despues}")

            # 7. Distribución por año
            print(f"\n📆 Distribución por año:")

            anios_query = (
                select(
                    func.extract('year', Evento.fecha_minima_evento).label('anio'),
                    func.count(func.distinct(Evento.id)).label('cantidad')
                )
                .select_from(
                    base_query.where(Evento.fecha_minima_evento.isnot(None)).subquery()
                )
                .group_by(func.extract('year', Evento.fecha_minima_evento))
                .order_by(func.extract('year', Evento.fecha_minima_evento))
            )
            anios_result = await db.execute(anios_query)
            anios = anios_result.all()

            for anio, cantidad in anios:
                anio_int = int(anio) if anio else 0
                print(f"   {anio_int}: {cantidad} eventos")

            # 8. Verificación
            print(f"\n🔍 VERIFICACIÓN:")
            print(f"   Sin fecha: {sin_fecha}")
            print(f"   Antes de rango: {antes}")
            print(f"   En rango: {en_rango}")
            print(f"   Después de rango: {despues}")
            print(f"   ────────────────────")
            print(f"   SUMA: {sin_fecha + antes + en_rango + despues}")
            print(f"   TOTAL ESPERADO: {total}")
            print(f"   COINCIDE: {'✅' if (sin_fecha + antes + en_rango + despues) == total else '❌'}")

            print(f"\n{'='*60}\n")

        finally:
            await db.close()
            break


if __name__ == "__main__":
    asyncio.run(analyze_dengue_dates())

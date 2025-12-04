"""
Servicio centralizado para queries de boletines epidemiológicos.
Todas las queries retornan datos estructurados listos para renderizar.
"""

import logging
from datetime import date, timedelta
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.boletines.models import CapacidadHospitalaria, VirusRespiratorio
from app.domains.eventos_epidemiologicos.eventos.models import (
    Evento,
    GrupoEno,
    TipoEno,
    TipoEnoGrupoEno,
)

logger = logging.getLogger(__name__)


class BoletinQueryService:
    """
    Servicio centralizado para queries de boletines.
    Todas las queries retornan datos limpios y estructurados.
    """

    @staticmethod
    async def query_top_enos(
        db: AsyncSession,
        limit: int,
        fecha_inicio: date,
        fecha_fin: date
    ) -> list[dict[str, Any]]:
        """
        Top N ENOs del período ordenados por casos.

        Args:
            db: Sesión de base de datos
            limit: Número máximo de ENOs a retornar
            fecha_inicio: Fecha inicio del período
            fecha_fin: Fecha fin del período

        Returns:
            [
                {
                    "tipo_eno_id": 1,
                    "tipo_eno_nombre": "Dengue",
                    "grupo_eno_id": 2,
                    "grupo_eno_nombre": "Vectoriales",
                    "casos_actuales": 245,
                    "casos_previos": 180,
                    "cambio_absoluto": 65,
                    "cambio_porcentual": 36.1,
                    "tendencia": "crecimiento"
                },
                ...
            ]
        """
        logger.info(
            f"Query top {limit} ENOs desde {fecha_inicio} hasta {fecha_fin}"
        )

        # Calcular período anterior (mismo número de días)
        dias_periodo = (fecha_fin - fecha_inicio).days
        fecha_inicio_anterior = fecha_inicio - timedelta(days=dias_periodo)
        fecha_fin_anterior = fecha_inicio - timedelta(days=1)

        # Query casos actuales
        stmt_actual = (
            select(
                TipoEno.id.label("tipo_eno_id"),
                TipoEno.nombre.label("tipo_eno_nombre"),
                GrupoEno.id.label("grupo_eno_id"),
                GrupoEno.nombre.label("grupo_eno_nombre"),
                func.count(Evento.id).label("casos_actuales")
            )
            .select_from(Evento)
            .join(TipoEno, Evento.id_tipo_eno == TipoEno.id)
            .join(TipoEnoGrupoEno, TipoEno.id == TipoEnoGrupoEno.id_tipo_eno)
            .join(GrupoEno, TipoEnoGrupoEno.id_grupo_eno == GrupoEno.id)
            .where(
                and_(
                    Evento.fecha_minima_evento >= fecha_inicio,
                    Evento.fecha_minima_evento <= fecha_fin
                )
            )
            .group_by(TipoEno.id, TipoEno.nombre, GrupoEno.id, GrupoEno.nombre)
            .order_by(func.count(Evento.id).desc())
            .limit(limit)
        )

        result_actual = await db.execute(stmt_actual)
        rows_actual = result_actual.all()

        # Query casos previos para los mismos ENOs
        tipo_eno_ids = [row.tipo_eno_id for row in rows_actual]

        if not tipo_eno_ids:
            return []

        stmt_previo = (
            select(
                TipoEno.id.label("tipo_eno_id"),
                func.count(Evento.id).label("casos_previos")
            )
            .select_from(Evento)
            .join(TipoEno, Evento.id_tipo_eno == TipoEno.id)
            .where(
                and_(
                    TipoEno.id.in_(tipo_eno_ids),
                    Evento.fecha_minima_evento >= fecha_inicio_anterior,
                    Evento.fecha_minima_evento <= fecha_fin_anterior
                )
            )
            .group_by(TipoEno.id)
        )

        result_previo = await db.execute(stmt_previo)
        rows_previo = {row.tipo_eno_id: row.casos_previos for row in result_previo.all()}

        # Combinar resultados
        top_enos = []
        for row in rows_actual:
            casos_actuales = int(row.casos_actuales)
            casos_previos = rows_previo.get(row.tipo_eno_id, 0)
            cambio_absoluto = casos_actuales - casos_previos
            cambio_porcentual = (
                (cambio_absoluto / casos_previos * 100)
                if casos_previos > 0
                else 0.0
            )

            # Determinar tendencia
            if cambio_porcentual > 10:
                tendencia = "crecimiento"
            elif cambio_porcentual < -10:
                tendencia = "descenso"
            else:
                tendencia = "estable"

            top_enos.append({
                "tipo_eno_id": row.tipo_eno_id,
                "tipo_eno_nombre": row.tipo_eno_nombre,
                "grupo_eno_id": row.grupo_eno_id,
                "grupo_eno_nombre": row.grupo_eno_nombre,
                "casos_actuales": casos_actuales,
                "casos_previos": casos_previos,
                "cambio_absoluto": cambio_absoluto,
                "cambio_porcentual": round(cambio_porcentual, 1),
                "tendencia": tendencia
            })

        logger.info(f"✓ Top {len(top_enos)} ENOs obtenidos")
        return top_enos

    @staticmethod
    async def query_evento_detail(
        db: AsyncSession,
        evento_id: int,
        fecha_inicio: date,
        fecha_fin: date
    ) -> dict[str, Any]:
        """
        Datos detallados de un evento específico.

        Args:
            db: Sesión de base de datos
            evento_id: ID del tipo de ENO
            fecha_inicio: Fecha inicio del período
            fecha_fin: Fecha fin del período

        Returns:
            {
                "tipo_eno_id": 1,
                "tipo_eno_nombre": "Dengue",
                "grupo_eno_id": 2,
                "grupo_eno_nombre": "Vectoriales",
                "casos_totales": 245,
                "distribucion_edad": [...],
                "distribucion_geografica": [...],
                "casos_por_semana": [...]
            }
        """
        logger.info(
            f"Query detalle evento {evento_id} desde {fecha_inicio} hasta {fecha_fin}"
        )

        # Obtener info básica del evento
        stmt_basico = (
            select(
                TipoEno.id,
                TipoEno.nombre,
                GrupoEno.id.label("grupo_id"),
                GrupoEno.nombre.label("grupo_nombre")
            )
            .select_from(TipoEno)
            .join(TipoEnoGrupoEno, TipoEno.id == TipoEnoGrupoEno.id_tipo_eno)
            .join(GrupoEno, TipoEnoGrupoEno.id_grupo_eno == GrupoEno.id)
            .where(TipoEno.id == evento_id)
        )

        result_basico = await db.execute(stmt_basico)
        row_basico = result_basico.first()

        if not row_basico:
            logger.warning(f"Evento {evento_id} no encontrado")
            return {}

        # Contar casos totales
        stmt_total = (
            select(func.count(Evento.id))
            .where(
                and_(
                    Evento.id_tipo_eno == evento_id,
                    Evento.fecha_minima_evento >= fecha_inicio,
                    Evento.fecha_minima_evento <= fecha_fin
                )
            )
        )

        result_total = await db.execute(stmt_total)
        casos_totales = result_total.scalar() or 0

        evento_detail = {
            "tipo_eno_id": row_basico.id,
            "tipo_eno_nombre": row_basico.nombre,
            "grupo_eno_id": row_basico.grupo_id,
            "grupo_eno_nombre": row_basico.grupo_nombre,
            "casos_totales": int(casos_totales),
            "distribucion_edad": [],  # Se puede agregar después
            "distribucion_geografica": [],  # Se puede agregar después
            "casos_por_semana": []  # Se puede agregar después
        }

        logger.info(f"✓ Detalle evento {evento_id}: {casos_totales} casos")
        return evento_detail

    @staticmethod
    async def query_capacidad_hospitalaria(
        db: AsyncSession,
        semana: int,
        anio: int
    ) -> list[dict[str, Any]]:
        """
        Capacidad hospitalaria por UGD para una semana específica.

        Args:
            db: Sesión de base de datos
            semana: Semana epidemiológica
            anio: Año

        Returns:
            [
                {
                    "ugd": "Norte",
                    "camas_totales": 150,
                    "camas_ocupadas": 120,
                    "porcentaje_ocupacion": 80.0
                },
                ...
            ]
        """
        logger.info(f"Query capacidad hospitalaria SE {semana}/{anio}")

        stmt = (
            select(CapacidadHospitalaria)
            .where(
                and_(
                    CapacidadHospitalaria.semana_epidemiologica == semana,
                    CapacidadHospitalaria.anio == anio
                )
            )
            .order_by(CapacidadHospitalaria.ugd)
        )

        result = await db.execute(stmt)
        rows = result.scalars().all()

        capacidad = [
            {
                "ugd": row.ugd,
                "camas_totales": row.camas_totales,
                "camas_ocupadas": row.camas_ocupadas,
                "porcentaje_ocupacion": round(row.porcentaje_ocupacion, 1)
            }
            for row in rows
        ]

        if not capacidad:
            logger.warning(f"No hay datos de capacidad para SE {semana}/{anio}")

        logger.info(f"✓ Capacidad hospitalaria: {len(capacidad)} UGDs")
        return capacidad

    @staticmethod
    async def query_virus_respiratorios(
        db: AsyncSession,
        semana: int,
        anio: int
    ) -> list[dict[str, Any]]:
        """
        Detección de virus respiratorios para una semana específica.

        Args:
            db: Sesión de base de datos
            semana: Semana epidemiológica
            anio: Año

        Returns:
            [
                {
                    "virus_tipo": "Influenza A",
                    "casos_positivos": 45,
                    "casos_testeados": 200,
                    "porcentaje_positividad": 22.5
                },
                ...
            ]
        """
        logger.info(f"Query virus respiratorios SE {semana}/{anio}")

        stmt = (
            select(VirusRespiratorio)
            .where(
                and_(
                    VirusRespiratorio.semana_epidemiologica == semana,
                    VirusRespiratorio.anio == anio
                )
            )
            .order_by(VirusRespiratorio.virus_tipo)
        )

        result = await db.execute(stmt)
        rows = result.scalars().all()

        virus = [
            {
                "virus_tipo": row.virus_tipo,
                "casos_positivos": row.casos_positivos,
                "casos_testeados": row.casos_testeados,
                "porcentaje_positividad": round(row.porcentaje_positividad, 1)
            }
            for row in rows
        ]

        if not virus:
            logger.warning(f"No hay datos de virus para SE {semana}/{anio}")

        logger.info(f"✓ Virus respiratorios: {len(virus)} tipos")
        return virus

    @staticmethod
    async def query_comparacion_periodos(
        db: AsyncSession,
        evento_id: int,
        periodo_actual: tuple[date, date],
        periodo_anterior: tuple[date, date]
    ) -> dict[str, Any]:
        """
        Comparación de casos entre dos períodos.

        Args:
            db: Sesión de base de datos
            evento_id: ID del tipo de ENO
            periodo_actual: (fecha_inicio, fecha_fin) del período actual
            periodo_anterior: (fecha_inicio, fecha_fin) del período anterior

        Returns:
            {
                "casos_actuales": 245,
                "casos_previos": 180,
                "cambio_absoluto": 65,
                "cambio_porcentual": 36.1,
                "tendencia": "crecimiento"
            }
        """
        logger.info(f"Query comparación períodos evento {evento_id}")

        # Casos período actual
        stmt_actual = (
            select(func.count(Evento.id))
            .where(
                and_(
                    Evento.id_tipo_eno == evento_id,
                    Evento.fecha_minima_evento >= periodo_actual[0],
                    Evento.fecha_minima_evento <= periodo_actual[1]
                )
            )
        )

        result_actual = await db.execute(stmt_actual)
        casos_actuales = result_actual.scalar() or 0

        # Casos período anterior
        stmt_anterior = (
            select(func.count(Evento.id))
            .where(
                and_(
                    Evento.id_tipo_eno == evento_id,
                    Evento.fecha_minima_evento >= periodo_anterior[0],
                    Evento.fecha_minima_evento <= periodo_anterior[1]
                )
            )
        )

        result_anterior = await db.execute(stmt_anterior)
        casos_previos = result_anterior.scalar() or 0

        # Calcular cambios
        cambio_absoluto = casos_actuales - casos_previos
        cambio_porcentual = (
            (cambio_absoluto / casos_previos * 100)
            if casos_previos > 0
            else 0.0
        )

        # Determinar tendencia
        if cambio_porcentual > 10:
            tendencia = "crecimiento"
        elif cambio_porcentual < -10:
            tendencia = "descenso"
        else:
            tendencia = "estable"

        comparacion = {
            "casos_actuales": int(casos_actuales),
            "casos_previos": int(casos_previos),
            "cambio_absoluto": cambio_absoluto,
            "cambio_porcentual": round(cambio_porcentual, 1),
            "tendencia": tendencia
        }

        logger.info(f"✓ Comparación: {casos_actuales} vs {casos_previos} casos")
        return comparacion

    @staticmethod
    async def query_distribucion_geografica(
        db: AsyncSession,
        evento_id: int,
        fecha_inicio: date,
        fecha_fin: date
    ) -> list[dict[str, Any]]:
        """
        Distribución de casos por ubicación geográfica.

        Args:
            db: Sesión de base de datos
            evento_id: ID del tipo de ENO
            fecha_inicio: Fecha inicio del período
            fecha_fin: Fecha fin del período

        Returns:
            [
                {
                    "departamento": "Rawson",
                    "casos": 89,
                    "porcentaje": 36.3
                },
                ...
            ]
        """
        logger.info(f"Query distribución geográfica evento {evento_id}")

        # Nota: Esta query necesita acceso a la tabla de domicilios/departamentos
        # Por ahora retorno estructura vacía
        # TODO: Implementar cuando tengamos acceso a geografía

        logger.warning("Query distribución geográfica no implementada completamente")
        return []

    @staticmethod
    async def query_distribucion_edad(
        db: AsyncSession,
        evento_id: int,
        fecha_inicio: date,
        fecha_fin: date
    ) -> list[dict[str, Any]]:
        """
        Distribución de casos por grupo etario.

        Args:
            db: Sesión de base de datos
            evento_id: ID del tipo de ENO
            fecha_inicio: Fecha inicio del período
            fecha_fin: date_fin del período

        Returns:
            [
                {
                    "grupo_edad": "0-4",
                    "casos": 45,
                    "porcentaje": 18.4
                },
                ...
            ]
        """
        logger.info(f"Query distribución edad evento {evento_id}")

        # Nota: Esta query necesita acceso a datos de persona/edad
        # Por ahora retorno estructura vacía
        # TODO: Implementar cuando tengamos acceso a datos de personas

        logger.warning("Query distribución edad no implementada completamente")
        return []

    @staticmethod
    async def query_eventos_agrupados(
        db: AsyncSession,
        tipo_evento: str,
        semana: int,
        anio: int,
        num_semanas: int = 4
    ) -> dict[str, Any]:
        """
        Datos de eventos agrupados para corredor endémico.

        Args:
            db: Sesión de base de datos
            tipo_evento: Tipo ("ETI", "Neumonía", "Bronquiolitis", "Diarreas")
            semana: Semana epidemiológica actual
            anio: Año
            num_semanas: Número de semanas a incluir en el análisis

        Returns:
            {
                "evento": "ETI",
                "semana_actual": 20,
                "casos_semana_actual": 450,
                "corredor": {
                    "zona_exito": [200, 300],
                    "zona_seguridad": [300, 400],
                    "zona_alerta": [400, 500],
                    "zona_epidemia": [500, 600]
                },
                "historico": [...]
            }
        """
        logger.info(f"Query eventos agrupados {tipo_evento} SE {semana}/{anio}")

        # Nota: Los eventos agrupados requieren una tabla específica
        # o lógica de agregación especial
        # Por ahora retorno estructura vacía
        # TODO: Implementar cuando tengamos datos de eventos agrupados

        logger.warning(f"Query eventos agrupados {tipo_evento} no implementada completamente")
        return {
            "evento": tipo_evento,
            "semana_actual": semana,
            "casos_semana_actual": 0,
            "corredor": {
                "zona_exito": [0, 0],
                "zona_seguridad": [0, 0],
                "zona_alerta": [0, 0],
                "zona_epidemia": [0, 0]
            },
            "historico": []
        }

    @staticmethod
    async def query_casos_semana(
        db: AsyncSession,
        evento_id: int,
        semana: int,
        anio: int
    ) -> int:
        """
        Cuenta casos de un evento para una semana específica.

        Args:
            db: Sesión de base de datos
            evento_id: ID del tipo de ENO
            semana: Semana epidemiológica
            anio: Año

        Returns:
            Número de casos en esa semana
        """
        from app.api.v1.analytics.period_utils import get_epi_week_dates

        logger.info(f"Query casos semana evento {evento_id} SE {semana}/{anio}")

        # Calcular fechas de la semana epidemiológica
        fecha_inicio, fecha_fin = get_epi_week_dates(semana, anio)

        stmt = (
            select(func.count(Evento.id))
            .where(
                and_(
                    Evento.id_tipo_eno == evento_id,
                    Evento.fecha_minima_evento >= fecha_inicio,
                    Evento.fecha_minima_evento <= fecha_fin
                )
            )
        )

        result = await db.execute(stmt)
        casos = result.scalar() or 0

        logger.info(f"✓ Casos SE {semana}/{anio}: {casos}")
        return int(casos)

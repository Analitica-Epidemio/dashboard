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
from app.domains.vigilancia_nominal.models.enfermedad import (
    Enfermedad,
    GrupoDeEnfermedades,
    EnfermedadGrupo,
)
from app.domains.vigilancia_nominal.models.caso import CasoEpidemiologico

logger = logging.getLogger(__name__)


class BoletinQueryService:
    """
    Servicio centralizado para queries de boletines.
    Todas las queries retornan datos limpios y estructurados.
    """

    @staticmethod
    async def consultar_top_enos(
        db: AsyncSession,
        limite: int,
        fecha_inicio: date,
        fecha_fin: date
    ) -> list[dict[str, Any]]:
        """
        Top N ENOs del período ordenados por casos.

        Args:
            db: Sesión de base de datos
            limite: Número máximo de ENOs a retornar
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
            f"Query top {limite} ENOs desde {fecha_inicio} hasta {fecha_fin}"
        )

        # Calcular período anterior (mismo número de días)
        dias_periodo = (fecha_fin - fecha_inicio).days
        fecha_inicio_anterior = fecha_inicio - timedelta(days=dias_periodo)
        fecha_fin_anterior = fecha_inicio - timedelta(days=1)

        # Query casos actuales
        stmt_actual = (
            select(
                Enfermedad.id.label("tipo_eno_id"),
                Enfermedad.nombre.label("tipo_eno_nombre"),
                GrupoDeEnfermedades.id.label("grupo_eno_id"),
                GrupoDeEnfermedades.nombre.label("grupo_eno_nombre"),
                func.count(CasoEpidemiologico.id).label("casos_actuales")
            )
            .select_from(CasoEpidemiologico)
            .join(Enfermedad, CasoEpidemiologico.id_enfermedad == Enfermedad.id)
            .join(EnfermedadGrupo, Enfermedad.id == EnfermedadGrupo.id_enfermedad)
            .join(GrupoDeEnfermedades, EnfermedadGrupo.id_grupo == GrupoDeEnfermedades.id)
            .where(
                and_(
                    CasoEpidemiologico.fecha_minima_caso >= fecha_inicio,
                    CasoEpidemiologico.fecha_minima_caso <= fecha_fin
                )
            )
            .group_by(Enfermedad.id, Enfermedad.nombre, GrupoDeEnfermedades.id, GrupoDeEnfermedades.nombre)
            .order_by(func.count(CasoEpidemiologico.id).desc())
            .limit(limite)
        )

        resultado_actual = await db.execute(stmt_actual)
        filas_actual = resultado_actual.all()

        # Query casos previos para los mismos ENOs
        ids_tipo_eno = [fila.tipo_eno_id for fila in filas_actual]

        if not ids_tipo_eno:
            return []

        stmt_previo = (
            select(
                Enfermedad.id.label("tipo_eno_id"),
                func.count(CasoEpidemiologico.id).label("casos_previos")
            )
            .select_from(CasoEpidemiologico)
            .join(Enfermedad, CasoEpidemiologico.id_enfermedad == Enfermedad.id)
            .where(
                and_(
                    Enfermedad.id.in_(ids_tipo_eno),
                    CasoEpidemiologico.fecha_minima_caso >= fecha_inicio_anterior,
                    CasoEpidemiologico.fecha_minima_caso <= fecha_fin_anterior
                )
            )
            .group_by(Enfermedad.id)
        )

        resultado_previo = await db.execute(stmt_previo)
        filas_previo = {fila.tipo_eno_id: fila.casos_previos for fila in resultado_previo.all()}

        # Combinar resultados
        top_enos = []
        for fila in filas_actual:
            casos_actuales = int(fila.casos_actuales)
            casos_previos = filas_previo.get(fila.tipo_eno_id, 0)
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
                "tipo_eno_id": fila.tipo_eno_id,
                "tipo_eno_nombre": fila.tipo_eno_nombre,
                "grupo_eno_id": fila.grupo_eno_id,
                "grupo_eno_nombre": fila.grupo_eno_nombre,
                "casos_actuales": casos_actuales,
                "casos_previos": casos_previos,
                "cambio_absoluto": cambio_absoluto,
                "cambio_porcentual": round(cambio_porcentual, 1),
                "tendencia": tendencia
            })

        logger.info(f"✓ Top {len(top_enos)} ENOs obtenidos")
        return top_enos

    @staticmethod
    async def consultar_detalle_evento(
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

        # Obtener info basica del evento
        stmt_basico = (
            select(
                Enfermedad.id,
                Enfermedad.nombre,
                GrupoDeEnfermedades.id.label("grupo_id"),
                GrupoDeEnfermedades.nombre.label("grupo_nombre")
            )
            .select_from(Enfermedad)
            .join(EnfermedadGrupo, Enfermedad.id == EnfermedadGrupo.id_enfermedad)
            .join(GrupoDeEnfermedades, EnfermedadGrupo.id_grupo == GrupoDeEnfermedades.id)
            .where(Enfermedad.id == evento_id)
        )

        resultado_basico = await db.execute(stmt_basico)
        fila_basico = resultado_basico.first()

        if not fila_basico:
            logger.warning(f"CasoEpidemiologico {evento_id} no encontrado")
            return {}

        # Contar casos totales
        stmt_total = (
            select(func.count(CasoEpidemiologico.id))
            .where(
                and_(
                    CasoEpidemiologico.id_enfermedad == evento_id,
                    CasoEpidemiologico.fecha_minima_caso >= fecha_inicio,
                    CasoEpidemiologico.fecha_minima_caso <= fecha_fin
                )
            )
        )

        resultado_total = await db.execute(stmt_total)
        casos_totales = resultado_total.scalar() or 0

        detalle_evento = {
            "tipo_eno_id": fila_basico.id,
            "tipo_eno_nombre": fila_basico.nombre,
            "grupo_eno_id": fila_basico.grupo_id,
            "grupo_eno_nombre": fila_basico.grupo_nombre,
            "casos_totales": int(casos_totales),
            "distribucion_edad": [],  # Se puede agregar después
            "distribucion_geografica": [],  # Se puede agregar después
            "casos_por_semana": []  # Se puede agregar después
        }

        logger.info(f"✓ Detalle evento {evento_id}: {casos_totales} casos")
        return detalle_evento

    @staticmethod
    async def consultar_capacidad_hospitalaria(
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

        resultado = await db.execute(stmt)
        filas = resultado.scalars().all()

        capacidad = [
            {
                "ugd": fila.ugd,
                "camas_totales": fila.camas_totales,
                "camas_ocupadas": fila.camas_ocupadas,
                "porcentaje_ocupacion": round(fila.porcentaje_ocupacion, 1)
            }
            for fila in filas
        ]

        if not capacidad:
            logger.warning(f"No hay datos de capacidad para SE {semana}/{anio}")

        logger.info(f"✓ Capacidad hospitalaria: {len(capacidad)} UGDs")
        return capacidad

    @staticmethod
    async def consultar_virus_respiratorios(
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

        resultado = await db.execute(stmt)
        filas = resultado.scalars().all()

        virus = [
            {
                "virus_tipo": fila.virus_tipo,
                "casos_positivos": fila.casos_positivos,
                "casos_testeados": fila.casos_testeados,
                "porcentaje_positividad": round(fila.porcentaje_positividad, 1)
            }
            for fila in filas
        ]

        if not virus:
            logger.warning(f"No hay datos de virus para SE {semana}/{anio}")

        logger.info(f"✓ Virus respiratorios: {len(virus)} tipos")
        return virus

    @staticmethod
    async def consultar_comparacion_periodos(
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
            select(func.count(CasoEpidemiologico.id))
            .where(
                and_(
                    CasoEpidemiologico.id_enfermedad == evento_id,
                    CasoEpidemiologico.fecha_minima_caso >= periodo_actual[0],
                    CasoEpidemiologico.fecha_minima_caso <= periodo_actual[1]
                )
            )
        )

        resultado_actual = await db.execute(stmt_actual)
        casos_actuales = resultado_actual.scalar() or 0

        # Casos período anterior
        stmt_anterior = (
            select(func.count(CasoEpidemiologico.id))
            .where(
                and_(
                    CasoEpidemiologico.id_enfermedad == evento_id,
                    CasoEpidemiologico.fecha_minima_caso >= periodo_anterior[0],
                    CasoEpidemiologico.fecha_minima_caso <= periodo_anterior[1]
                )
            )
        )

        resultado_anterior = await db.execute(stmt_anterior)
        casos_previos = resultado_anterior.scalar() or 0

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
    async def consultar_distribucion_geografica(
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
    async def consultar_distribucion_edad(
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
    async def consultar_eventos_agrupados(
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
    async def consultar_casos_semana(
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
            select(func.count(CasoEpidemiologico.id))
            .where(
                and_(
                    CasoEpidemiologico.id_enfermedad == evento_id,
                    CasoEpidemiologico.fecha_minima_caso >= fecha_inicio,
                    CasoEpidemiologico.fecha_minima_caso <= fecha_fin
                )
            )
        )

        resultado = await db.execute(stmt)
        casos = resultado.scalar() or 0

        logger.info(f"✓ Casos SE {semana}/{anio}: {casos}")
        return int(casos)

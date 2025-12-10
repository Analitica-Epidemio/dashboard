"""
Servicio de Insights para Boletines Epidemiológicos.

Genera texto descriptivo automático basado en datos estadísticos.
Por ejemplo:
- "De los 24 casos notificados de Dengue, el mayor porcentaje (25%) corresponde al grupo de 25-34 años"
- "El departamento con mayor incidencia es Rawson con 45 casos (36.3%)"
"""

import logging
from datetime import date
from typing import Any, Optional

from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.domains.dashboard.age_groups_config import (
    generar_sql_case_when,
    obtener_configuracion_grupos_edad,
)
from app.domains.vigilancia_nominal.models.caso import CasoEpidemiologico
from app.domains.vigilancia_nominal.models.enfermedad import Enfermedad

logger = logging.getLogger(__name__)


class BoletinInsightsService:
    """
    Servicio para generar insights (texto descriptivo) automáticos
    basados en datos de eventos epidemiológicos.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generar_insight_distribucion_edad(
        self,
        evento_id: int,
        fecha_inicio: date,
        fecha_fin: date,
        evento_nombre: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Genera insight sobre distribución por edad.

        Ejemplo de texto generado:
        "De los 24 casos notificados de Dengue, el mayor porcentaje (25%)
        corresponde al grupo de 25-34 años, seguido del grupo de 15-24 años (20.8%)."

        Args:
            evento_id: ID del tipo de ENO
            fecha_inicio: Fecha inicio del período
            fecha_fin: Fecha fin del período
            evento_nombre: Nombre del evento (opcional, se obtiene de DB si no se pasa)

        Returns:
            {
                "texto": "De los 24 casos...",
                "total_casos": 24,
                "grupo_mayor": {"grupo": "25-34", "casos": 6, "porcentaje": 25.0},
                "grupos": [...]
            }
        """
        # Obtener nombre del evento si no se pasó
        if not evento_nombre:
            stmt = select(col(Enfermedad.nombre)).where(col(Enfermedad.id) == evento_id)
            result = await self.db.execute(stmt)
            row = result.scalar_one_or_none()
            evento_nombre = row if row else f"evento {evento_id}"

        # Configuración de grupos de edad
        config_grupos_edad = obtener_configuracion_grupos_edad("standard")
        sql_case_when = generar_sql_case_when(config_grupos_edad)

        query = f"""
        SELECT
            {sql_case_when} as grupo_edad,
            COUNT(*) as casos
        FROM caso_epidemiologico e
        WHERE e.id_enfermedad = :evento_id
          AND e.fecha_minima_caso >= :fecha_inicio
          AND e.fecha_minima_caso <= :fecha_fin
          AND e.fecha_nacimiento IS NOT NULL
          AND e.fecha_minima_caso IS NOT NULL
        GROUP BY grupo_edad
        ORDER BY casos DESC
        """

        result = await self.db.execute(
            text(query),
            {
                "evento_id": evento_id,
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
            },
        )
        filas = result.fetchall()

        if not filas:
            return {
                "texto": f"No se encontraron datos de distribución por edad para {evento_nombre}.",
                "total_casos": 0,
                "grupo_mayor": None,
                "grupos": [],
            }

        # Calcular totales y porcentajes
        total_casos = sum(fila[1] for fila in filas)
        grupos = []
        for fila in filas:
            grupo_edad, casos = fila
            if grupo_edad == "Desconocido":
                continue
            porcentaje = (casos / total_casos * 100) if total_casos > 0 else 0
            grupos.append(
                {
                    "grupo": grupo_edad,
                    "casos": casos,
                    "porcentaje": round(porcentaje, 1),
                }
            )

        # Ordenar por casos (mayor a menor)
        grupos.sort(key=lambda x: x["casos"], reverse=True)

        # Generar texto
        if grupos:
            grupo_mayor = grupos[0]
            texto = (
                f"De los {total_casos} casos notificados de {evento_nombre}, "
                f"el mayor porcentaje ({grupo_mayor['porcentaje']}%) corresponde al grupo de "
                f"{grupo_mayor['grupo']} años"
            )

            # Agregar segundo grupo si existe y es significativo
            if len(grupos) > 1 and grupos[1]["porcentaje"] >= 10:
                texto += f", seguido del grupo de {grupos[1]['grupo']} años ({grupos[1]['porcentaje']}%)"

            texto += "."
        else:
            texto = f"No se encontraron datos de distribución por edad para {evento_nombre}."
            grupo_mayor = None

        return {
            "texto": texto,
            "total_casos": total_casos,
            "grupo_mayor": grupo_mayor,
            "grupos": grupos,
        }

    async def generar_insight_distribucion_geografica(
        self,
        evento_id: int,
        fecha_inicio: date,
        fecha_fin: date,
        evento_nombre: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Genera insight sobre distribución geográfica.

        Ejemplo de texto generado:
        "El departamento con mayor número de casos es Rawson con 45 casos (36.3%),
        seguido de Trelew con 30 casos (24.4%)."

        Args:
            evento_id: ID del tipo de ENO
            fecha_inicio: Fecha inicio del período
            fecha_fin: Fecha fin del período
            evento_nombre: Nombre del evento (opcional)

        Returns:
            {
                "texto": "El departamento con mayor...",
                "total_casos": 123,
                "departamento_mayor": {"nombre": "Rawson", "casos": 45, "porcentaje": 36.3},
                "departamentos": [...]
            }
        """
        if not evento_nombre:
            stmt = select(col(Enfermedad.nombre)).where(col(Enfermedad.id) == evento_id)
            result = await self.db.execute(stmt)
            row = result.scalar_one_or_none()
            evento_nombre = row if row else f"evento {evento_id}"

        query = """
        SELECT
            COALESCE(d.nombre, 'Sin especificar') as departamento,
            COUNT(DISTINCT e.id) as casos
        FROM caso_epidemiologico e
        LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
        LEFT JOIN localidad l ON est.id_localidad_indec = l.id_localidad_indec
        LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
        WHERE e.id_enfermedad = :evento_id
          AND e.fecha_minima_caso >= :fecha_inicio
          AND e.fecha_minima_caso <= :fecha_fin
        GROUP BY d.nombre
        ORDER BY casos DESC
        """

        result = await self.db.execute(
            text(query),
            {
                "evento_id": evento_id,
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
            },
        )
        filas = result.fetchall()

        if not filas:
            return {
                "texto": f"No se encontraron datos de distribución geográfica para {evento_nombre}.",
                "total_casos": 0,
                "departamento_mayor": None,
                "departamentos": [],
            }

        total_casos = sum(fila[1] for fila in filas)
        departamentos = []
        for fila in filas:
            nombre, casos = fila
            if nombre == "Sin especificar":
                continue
            porcentaje = (casos / total_casos * 100) if total_casos > 0 else 0
            departamentos.append(
                {"nombre": nombre, "casos": casos, "porcentaje": round(porcentaje, 1)}
            )

        departamentos.sort(key=lambda x: x["casos"], reverse=True)

        if departamentos:
            depto_mayor = departamentos[0]
            texto = (
                f"El departamento con mayor número de casos es {depto_mayor['nombre']} "
                f"con {depto_mayor['casos']} casos ({depto_mayor['porcentaje']}%)"
            )

            if len(departamentos) > 1 and departamentos[1]["porcentaje"] >= 10:
                texto += f", seguido de {departamentos[1]['nombre']} con {departamentos[1]['casos']} casos ({departamentos[1]['porcentaje']}%)"

            texto += "."
        else:
            texto = f"No se encontraron datos de distribución geográfica para {evento_nombre}."
            depto_mayor = None

        return {
            "texto": texto,
            "total_casos": total_casos,
            "departamento_mayor": depto_mayor,
            "departamentos": departamentos,
        }

    async def generar_insight_tendencia(
        self,
        evento_id: int,
        semana_actual: int,
        anio: int,
        num_semanas: int = 4,
        evento_nombre: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Genera insight sobre tendencia temporal.

        Ejemplo de texto generado:
        "Se observa un incremento del 25% en los casos de Dengue respecto
        al período anterior (semanas 16-19 vs 12-15)."

        Args:
            evento_id: ID del tipo de ENO
            semana_actual: Semana epidemiológica actual
            anio: Año
            num_semanas: Número de semanas del período de análisis
            evento_nombre: Nombre del evento (opcional)

        Returns:
            {
                "texto": "Se observa un incremento...",
                "casos_periodo_actual": 100,
                "casos_periodo_anterior": 80,
                "variacion_porcentual": 25.0,
                "tendencia": "aumento" | "descenso" | "estable"
            }
        """
        from app.api.v1.analytics.period_utils import get_epi_week_dates

        if not evento_nombre:
            stmt = select(col(Enfermedad.nombre)).where(col(Enfermedad.id) == evento_id)
            result = await self.db.execute(stmt)
            row = result.scalar_one_or_none()
            evento_nombre = row if row else f"evento {evento_id}"

        # Calcular período actual
        semana_inicio_actual = semana_actual - num_semanas + 1
        anio_inicio_actual = anio
        if semana_inicio_actual < 1:
            semana_inicio_actual += 52
            anio_inicio_actual -= 1

        fecha_inicio_actual, _ = get_epi_week_dates(
            semana_inicio_actual, anio_inicio_actual
        )
        _, fecha_fin_actual = get_epi_week_dates(semana_actual, anio)

        # Calcular período anterior
        semana_fin_anterior = semana_inicio_actual - 1
        anio_fin_anterior = anio_inicio_actual
        if semana_fin_anterior < 1:
            semana_fin_anterior = 52
            anio_fin_anterior -= 1

        semana_inicio_anterior = semana_fin_anterior - num_semanas + 1
        anio_inicio_anterior = anio_fin_anterior
        if semana_inicio_anterior < 1:
            semana_inicio_anterior += 52
            anio_inicio_anterior -= 1

        fecha_inicio_anterior, _ = get_epi_week_dates(
            semana_inicio_anterior, anio_inicio_anterior
        )
        _, fecha_fin_anterior = get_epi_week_dates(
            semana_fin_anterior, anio_fin_anterior
        )

        # Query casos período actual
        stmt_actual = select(func.count(CasoEpidemiologico.id)).where(
            and_(
                col(CasoEpidemiologico.id_enfermedad) == evento_id,
                col(CasoEpidemiologico.fecha_minima_caso) >= fecha_inicio_actual,
                col(CasoEpidemiologico.fecha_minima_caso) <= fecha_fin_actual,
            )
        )
        result_actual = await self.db.execute(stmt_actual)
        casos_actual = result_actual.scalar() or 0

        # Query casos período anterior
        stmt_anterior = select(func.count(CasoEpidemiologico.id)).where(
            and_(
                col(CasoEpidemiologico.id_enfermedad) == evento_id,
                col(CasoEpidemiologico.fecha_minima_caso) >= fecha_inicio_anterior,
                col(CasoEpidemiologico.fecha_minima_caso) <= fecha_fin_anterior,
            )
        )
        result_anterior = await self.db.execute(stmt_anterior)
        casos_anterior = result_anterior.scalar() or 0

        # Calcular variación
        if casos_anterior > 0:
            variacion = ((casos_actual - casos_anterior) / casos_anterior) * 100
        else:
            variacion = 100 if casos_actual > 0 else 0

        # Determinar tendencia
        if abs(variacion) < 5:
            tendencia = "estable"
            texto = (
                f"Los casos de {evento_nombre} se mantienen estables "
                f"({casos_actual} casos en SE {semana_inicio_actual}-{semana_actual} "
                f"vs {casos_anterior} en el período anterior)."
            )
        elif variacion > 0:
            tendencia = "aumento"
            texto = (
                f"Se observa un incremento del {abs(variacion):.0f}% en los casos de {evento_nombre} "
                f"respecto al período anterior "
                f"({casos_anterior} → {casos_actual} casos)."
            )
        else:
            tendencia = "descenso"
            texto = (
                f"Se observa una disminución del {abs(variacion):.0f}% en los casos de {evento_nombre} "
                f"respecto al período anterior "
                f"({casos_anterior} → {casos_actual} casos)."
            )

        return {
            "texto": texto,
            "casos_periodo_actual": int(casos_actual),
            "casos_periodo_anterior": int(casos_anterior),
            "variacion_porcentual": round(variacion, 1),
            "tendencia": tendencia,
            "periodo_actual": f"SE {semana_inicio_actual}-{semana_actual}/{anio}",
            "periodo_anterior": f"SE {semana_inicio_anterior}-{semana_fin_anterior}/{anio_fin_anterior}",
        }

    async def generar_insight_resumen(
        self,
        evento_id: int,
        fecha_inicio: date,
        fecha_fin: date,
        evento_nombre: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Genera un resumen completo combinando múltiples insights.

        Args:
            evento_id: ID del tipo de ENO
            fecha_inicio: Fecha inicio del período
            fecha_fin: Fecha fin del período
            evento_nombre: Nombre del evento (opcional)

        Returns:
            {
                "texto": "Texto completo del resumen...",
                "total_casos": 100,
                "insights": {
                    "edad": {...},
                    "geografia": {...}
                }
            }
        """
        if not evento_nombre:
            stmt = select(col(Enfermedad.nombre)).where(col(Enfermedad.id) == evento_id)
            result = await self.db.execute(stmt)
            row = result.scalar_one_or_none()
            evento_nombre = row if row else f"evento {evento_id}"

        # Obtener total de casos
        stmt_total = select(func.count(CasoEpidemiologico.id)).where(
            and_(
                col(CasoEpidemiologico.id_enfermedad) == evento_id,
                col(CasoEpidemiologico.fecha_minima_caso) >= fecha_inicio,
                col(CasoEpidemiologico.fecha_minima_caso) <= fecha_fin,
            )
        )
        result_total = await self.db.execute(stmt_total)
        total_casos = result_total.scalar() or 0

        if total_casos == 0:
            return {
                "texto": f"No se registraron casos de {evento_nombre} durante el período analizado.",
                "total_casos": 0,
                "insights": {},
            }

        # Obtener insights individuales
        insight_edad = await self.generar_insight_distribucion_edad(
            evento_id, fecha_inicio, fecha_fin, evento_nombre
        )
        insight_geo = await self.generar_insight_distribucion_geografica(
            evento_id, fecha_inicio, fecha_fin, evento_nombre
        )

        # Construir texto resumen
        partes = [
            f"Durante el período analizado se notificaron {total_casos} casos de {evento_nombre}."
        ]

        if insight_edad.get("grupo_mayor"):
            grupo = insight_edad["grupo_mayor"]
            partes.append(
                f"El grupo etario más afectado es {grupo['grupo']} años ({grupo['porcentaje']}%)."
            )

        if insight_geo.get("departamento_mayor"):
            dept = insight_geo["departamento_mayor"]
            partes.append(
                f"La mayor concentración de casos se encuentra en {dept['nombre']} ({dept['porcentaje']}%)."
            )

        return {
            "texto": " ".join(partes),
            "total_casos": total_casos,
            "insights": {"edad": insight_edad, "geografia": insight_geo},
        }

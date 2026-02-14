"""
Procesadores Python para charts dinámicos
Consulta datos reales de eventos desde la base de datos
"""

import logging
from datetime import date, datetime
from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.epidemiology import (
    calcular_semana_epidemiologica,
    obtener_fechas_semana_epidemiologica,
)
from app.domains.dashboard.age_groups_config import (
    generar_sql_case_when,
    obtener_configuracion_grupos_edad,
    obtener_etiquetas_grupos_edad,
)
from app.domains.vigilancia_nominal.models.agentes import ResultadoDeteccion

logger = logging.getLogger(__name__)


class ChartDataProcessor:
    """Procesador de datos para charts del dashboard"""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _parsear_fecha(self, date_str: str | None) -> date | None:
        """Convierte string de fecha a objeto date"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    def _aplicar_filtros_comunes(
        self, query: str, filtros: dict[str, Any], params: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """
        Aplica filtros comunes a las queries incluyendo clasificación

        Args:
            query: Query SQL base
            filtros: Filtros del dashboard
            params: Parámetros de la query

        Returns:
            Tupla con (query modificada, params actualizados)
        """
        if filtros.get("grupo_id"):
            query += """
                AND id_enfermedad IN (
                    SELECT id_enfermedad FROM enfermedad_grupo WHERE id_grupo = :grupo_id
                )
            """
            params["grupo_id"] = filtros["grupo_id"]

        if filtros.get("tipo_eno_ids"):
            tipo_eno_ids = filtros["tipo_eno_ids"]
            if tipo_eno_ids and len(tipo_eno_ids) > 0:
                query += " AND id_enfermedad = ANY(:tipo_eno_ids)"
                params["tipo_eno_ids"] = tipo_eno_ids

        # Filtro por clasificación estrategia
        if filtros.get("clasificaciones"):
            clasificaciones = filtros["clasificaciones"]
            if isinstance(clasificaciones, str):
                clasificaciones = [clasificaciones]
            query += " AND clasificacion_estrategia = ANY(:clasificaciones)"
            params["clasificaciones"] = clasificaciones

        if filtros.get("fecha_desde"):
            query += " AND fecha_minima_caso >= :fecha_desde"
            params["fecha_desde"] = self._parsear_fecha(filtros["fecha_desde"])

        if filtros.get("fecha_hasta"):
            query += " AND fecha_minima_caso <= :fecha_hasta"
            params["fecha_hasta"] = self._parsear_fecha(filtros["fecha_hasta"])

        return query, params

    def _agregar_filtro_clasificacion(
        self,
        query: str,
        filtros: dict[str, Any],
        params: dict[str, Any],
        table_alias: str = "",
    ) -> str:
        """Helper para agregar filtro de clasificación a cualquier query"""
        if filtros.get("clasificaciones"):
            clasificaciones = filtros["clasificaciones"]
            if isinstance(clasificaciones, str):
                clasificaciones = [clasificaciones]

            # Agregar alias de tabla si se proporciona
            field = (
                f"{table_alias}.clasificacion_estrategia"
                if table_alias
                else "clasificacion_estrategia"
            )
            query += f" AND {field} = ANY(:clasificaciones)"
            params["clasificaciones"] = clasificaciones

        return query

    def _agregar_filtro_provincia(
        self,
        query: str,
        filtros: dict[str, Any],
        params: dict[str, Any],
        table_alias: str = "d",
    ) -> tuple[str, dict[str, Any]]:
        """Helper para agregar filtro de provincia por código INDEC"""
        provincia_id = filtros.get("provincia_id")

        if provincia_id:
            query += f" AND {table_alias}.id_provincia_indec = :provincia_id"
            params["provincia_id"] = provincia_id
            logger.debug(f"🔍 Filtro provincia aplicado: {provincia_id}")
        else:
            logger.debug("🌍 Sin filtro de provincia - datos de TODAS las provincias")

        return query, params

    def _generar_metadata_semanal(self, rows: list) -> list:
        """
        Genera metadata de semanas epidemiológicas a partir de filas con (semana, año, ...)

        Args:
            rows: Lista de filas de query con formato (semana, año, ...)

        Returns:
            Lista de diccionarios con metadata de cada semana
        """
        if not rows:
            return []

        metadata = []
        for row in rows:
            semana = int(row[0])
            año = (
                int(row[1])
                if len(row) > 1 and row[1] is not None
                else datetime.now().year
            )

            try:
                start_date, end_date = obtener_fechas_semana_epidemiologica(año, semana)
                metadata.append(
                    {
                        "year": año,
                        "week": semana,
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d"),
                    }
                )
            except Exception as e:
                logger.warning(
                    f"Error generando metadata para semana {semana}/{año}: {e}"
                )
                continue

        return metadata

    async def procesar_grafico(
        self, chart_config: Any, filtros: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Procesa un chart según su función de procesamiento

        Args:
            chart_config: Configuración del chart desde DB
            filtros: Filtros aplicados desde el dashboard

        Returns:
            Dict con los datos procesados para el chart
        """
        from collections.abc import Awaitable, Callable

        # Mapear función de procesamiento
        processor_map: dict[
            str, Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]
        ] = {
            "curva_epidemiologica": self.procesar_curva_epidemiologica,
            "corredor_endemico": self.procesar_corredor_endemico,
            "piramide_poblacional": self.procesar_piramide_poblacional,
            "mapa_geografico": self.procesar_mapa_geografico,
            "estacionalidad": self.procesar_estacionalidad,
            "casos_edad": self.procesar_casos_edad,
            "intento_suicidio": self.procesar_intento_suicidio,
            "rabia_animal": self.procesar_rabia_animal,
            "proporcion_ira": self.procesar_proporcion_ira,
            "distribucion_clasificacion": self.procesar_distribucion_clasificacion,
        }

        processor_func = processor_map.get(chart_config.funcion_procesamiento)
        if not processor_func:
            logger.error(
                f"Función de procesamiento no encontrada: {chart_config.funcion_procesamiento}"
            )
            return {
                "error": f"Función de procesamiento no encontrada: {chart_config.funcion_procesamiento}"
            }

        # Ejecutar procesador
        try:
            logger.debug(
                f"Ejecutando procesador {chart_config.funcion_procesamiento} con filtros: {filtros}"
            )
            result = await processor_func(filtros)
            logger.debug(f"Procesador {chart_config.funcion_procesamiento} completado")
            return result
        except Exception as e:
            logger.error(
                f"Error en procesador {chart_config.funcion_procesamiento}: {e!s}"
            )
            # Retornar estructura vacía en caso de error
            return {
                "type": chart_config.tipo_visualizacion,
                "data": {"labels": [], "datasets": []},
                "error": str(e),
            }

    async def procesar_curva_epidemiologica(
        self,
        filtros: dict[str, Any],
        series_config: list[dict[str, Any]] | None = None,
        agrupar_por: str | None = None,
    ) -> dict[str, Any]:
        """
        Procesa curva epidemiológica con una o múltiples series.

        Args:
            filtros: Filtros base (fecha_desde, fecha_hasta, provincia_id, etc.)
                - agrupacion_temporal: "semana" | "mes" | "anio" (default: "semana")
            series_config: Lista de configuraciones de serie. Cada serie tiene:
                - tipo_eno_ids: Array de IDs de tipo_eno (se SUMAN para esta serie)
                - agente_codigos: Array de códigos de agente (para agrupar por agente)
                - label: Etiqueta para la leyenda
                - color: Color de la línea (hex o rgb)
            agrupar_por: "evento" | "agente" | None - cómo agrupar las series

        Returns:
            Dict con formato Chart.js (uno o múltiples datasets)
        """
        # Si agrupamos por agente, usar procesamiento especial
        if agrupar_por == "agente" and series_config:
            return await self._procesar_curva_por_agente(filtros, series_config)

        # Si no hay series_config, construir desde tipo_eno_ids de filtros
        if series_config is None:
            tipo_eno_ids = filtros.get("tipo_eno_ids", [])
            if tipo_eno_ids:
                series_config = [
                    {
                        "tipo_eno_ids": tipo_eno_ids,
                        "label": "Casos",
                        "color": "rgb(75, 192, 192)",
                    }
                ]
            else:
                series_config = []

        if not series_config:
            return {
                "type": "line",
                "data": {"labels": [], "datasets": [], "metadata": []},
                "error": "No se configuraron series para el gráfico",
            }

        # Determinar agrupación temporal
        agrupacion = filtros.get("agrupacion_temporal", "semana")

        # Configurar SELECT y GROUP BY según agrupación
        if agrupacion == "mes":
            select_periodo = """
                EXTRACT(MONTH FROM e.fecha_minima_caso)::int as periodo,
                EXTRACT(YEAR FROM e.fecha_minima_caso)::int as año
            """
            group_order = (
                "periodo, año, e.id_enfermedad ORDER BY año, periodo, e.id_enfermedad"
            )
        elif agrupacion == "anio":
            select_periodo = """
                EXTRACT(YEAR FROM e.fecha_minima_caso)::int as periodo,
                EXTRACT(YEAR FROM e.fecha_minima_caso)::int as año
            """
            group_order = "periodo, e.id_enfermedad ORDER BY periodo, e.id_enfermedad"
        else:  # semana (default)
            select_periodo = """
                e.fecha_minima_caso_semana_epi as periodo,
                e.fecha_minima_caso_anio_epi as año
            """
            group_order = (
                "periodo, año, e.id_enfermedad ORDER BY año, periodo, e.id_enfermedad"
            )

        # Extraer TODOS los IDs de todas las series (aplanar arrays)
        all_tipo_eno_ids = []
        for serie in series_config:
            all_tipo_eno_ids.extend(serie.get("tipo_eno_ids", []))

        # Eliminar duplicados manteniendo orden
        all_tipo_eno_ids = list(dict.fromkeys(all_tipo_eno_ids))

        if not all_tipo_eno_ids:
            return {
                "type": "line",
                "data": {"labels": [], "datasets": [], "metadata": []},
                "error": "No se encontraron IDs de eventos válidos",
            }

        # Query que agrupa por tipo_eno y período
        query = f"""
        SELECT
            {select_periodo},
            e.id_enfermedad,
            COUNT(*) as casos
        FROM caso_epidemiologico e
        """

        params = {"tipo_eno_ids": all_tipo_eno_ids}

        # Lazy Joins: Solo hacer JOINs geográficos si hay filtro de provincia
        if filtros.get("provincia_id"):
            query += """
            LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
            LEFT JOIN localidad l ON est.id_localidad_indec = l.id_localidad_indec
            LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
            """

        query += " WHERE e.id_enfermedad = ANY(:tipo_eno_ids)"

        # Filtro de provincia
        if filtros.get("provincia_id"):
            query, params = self._agregar_filtro_provincia(query, filtros, params, "d")

        # Filtro de clasificación
        query = self._agregar_filtro_clasificacion(query, filtros, params, "e")

        # Filtros de fecha
        if filtros.get("fecha_desde"):
            query += " AND e.fecha_minima_caso >= :fecha_desde"
            params["fecha_desde"] = self._parsear_fecha(filtros["fecha_desde"])

        if filtros.get("fecha_hasta"):
            query += " AND e.fecha_minima_caso <= :fecha_hasta"
            params["fecha_hasta"] = self._parsear_fecha(filtros["fecha_hasta"])

        query += f" GROUP BY {group_order}"

        # Ejecutar query
        result = await self.db.execute(text(query), params)
        rows = result.fetchall()

        logger.info(
            f"Curva epidemiológica ({agrupacion}) - {len(rows)} filas, {len(series_config)} series"
        )

        if not rows:
            return {
                "type": "line",
                "data": {"labels": [], "datasets": [], "metadata": []},
            }

        # Construir estructura de datos
        periodos_set: set[tuple[int, ...]] = set()
        datos_por_tipo = {}  # {tipo_eno_id: {(periodo, año): casos}}

        for row in rows:
            periodo, año, tipo_eno_id, casos = row
            if agrupacion == "anio":
                # Para año, el período y año son lo mismo
                periodos_set.add((int(periodo),))
                if tipo_eno_id not in datos_por_tipo:
                    datos_por_tipo[tipo_eno_id] = {}
                datos_por_tipo[tipo_eno_id][(int(periodo),)] = casos
            else:
                periodos_set.add((int(periodo), int(año)))
                if tipo_eno_id not in datos_por_tipo:
                    datos_por_tipo[tipo_eno_id] = {}
                datos_por_tipo[tipo_eno_id][(int(periodo), int(año))] = casos

        # Ordenar períodos cronológicamente y generar labels
        metadata: list[dict[str, Any]] = []

        if agrupacion == "anio":
            periodos_ordenados = sorted(periodos_set, key=lambda x: x[0])
            labels = [str(p[0]) for p in periodos_ordenados]
            metadata = [{"year": p[0]} for p in periodos_ordenados]
        elif agrupacion == "mes":
            meses_nombres = [
                "Ene",
                "Feb",
                "Mar",
                "Abr",
                "May",
                "Jun",
                "Jul",
                "Ago",
                "Sep",
                "Oct",
                "Nov",
                "Dic",
            ]
            periodos_ordenados = sorted(periodos_set, key=lambda x: (x[1], x[0]))
            labels = [f"{meses_nombres[p[0] - 1]} {p[1]}" for p in periodos_ordenados]
            metadata = [{"month": p[0], "year": p[1]} for p in periodos_ordenados]
        else:  # semana
            periodos_ordenados = sorted(periodos_set, key=lambda x: (x[1], x[0]))
            labels = [f"SE {p[0]}/{p[1]}" for p in periodos_ordenados]
            # metadata init var already done
            for periodo_tuple in periodos_ordenados:
                # Type guard implícito o ignore
                if len(periodo_tuple) >= 2:
                    p_semana, p_año = periodo_tuple[0], periodo_tuple[1]
                    try:
                        start_date, end_date = obtener_fechas_semana_epidemiologica(
                            p_año, p_semana
                        )
                        metadata.append(
                            {
                                "year": p_año,
                                "week": p_semana,
                                "start_date": start_date.strftime("%Y-%m-%d")
                                if start_date
                                else "",
                                "end_date": end_date.strftime("%Y-%m-%d")
                                if end_date
                                else "",
                            }
                        )
                    except Exception:
                        continue

        # Construir datasets para cada serie
        # NOTA: Ahora cada serie puede tener múltiples tipo_eno_ids que se SUMAN
        datasets = []
        for serie in series_config:
            serie_ids = serie.get("tipo_eno_ids", [])
            label = serie.get("label", "Serie")
            color = serie.get("color", "rgb(75, 192, 192)")

            # SUMAR datos de todos los tipo_eno_ids en esta serie
            data = []
            for periodo in periodos_ordenados:
                total_periodo = 0
                for tipo_eno_id in serie_ids:
                    datos_tipo = datos_por_tipo.get(tipo_eno_id, {})
                    total_periodo += datos_tipo.get(periodo, 0)
                data.append(total_periodo)

            datasets.append(
                {
                    "label": label,
                    "data": data,
                    "borderColor": color,
                    "backgroundColor": color,
                    "tension": 0.1,
                    "fill": False,
                }
            )

        return {
            "type": "line",
            "data": {"labels": labels, "datasets": datasets, "metadata": metadata},
        }

    async def _procesar_curva_por_agente(
        self, filtros: dict[str, Any], series_config: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Procesa curva epidemiológica agrupada por agentes etiológicos.

        Args:
            filtros: Filtros base (fecha_desde, fecha_hasta, etc.)
            series_config: Lista de configuraciones. Cada serie tiene:
                - agente_codigos: Array de códigos de agente (se SUMAN para esta serie)
                - label: Etiqueta para la leyenda
                - color: Color de la línea

        Returns:
            Dict con formato Chart.js
        """
        # Extraer TODOS los códigos de agentes de todas las series (aplanar arrays)
        all_agente_codigos = []
        for serie in series_config:
            all_agente_codigos.extend(serie.get("agente_codigos", []))

        # Eliminar duplicados manteniendo orden
        all_agente_codigos = list(dict.fromkeys(all_agente_codigos))

        if not all_agente_codigos:
            return {
                "type": "line",
                "data": {"labels": [], "datasets": [], "metadata": []},
                "error": "No se configuraron agentes para el gráfico",
            }

        # Query que agrupa por agente y semana epidemiológica
        query = """
        SELECT
            e.fecha_minima_caso_semana_epi as semana,
            e.fecha_minima_caso_anio_epi as anio,
            ae.slug as agente_codigo,
            COUNT(DISTINCT e.id) as casos
        FROM caso_epidemiologico e
        JOIN caso_agente ea ON e.id = ea.id_caso
        JOIN agente_etiologico ae ON ea.id_agente = ae.id
        WHERE ae.slug = ANY(:agente_codigos)
          AND ea.resultado = :resultado_positivo
        """

        params: dict[str, Any] = {
            "agente_codigos": all_agente_codigos,
            "resultado_positivo": ResultadoDeteccion.POSITIVO.value,
        }

        # Filtros de fecha
        if filtros.get("fecha_desde"):
            query += " AND e.fecha_minima_caso >= :fecha_desde"
            params["fecha_desde"] = self._parsear_fecha(filtros["fecha_desde"])

        if filtros.get("fecha_hasta"):
            query += " AND e.fecha_minima_caso <= :fecha_hasta"
            params["fecha_hasta"] = self._parsear_fecha(filtros["fecha_hasta"])

        query += (
            " GROUP BY semana, anio, agente_codigo ORDER BY anio, semana, agente_codigo"
        )

        result = await self.db.execute(text(query), params)
        rows = result.fetchall()

        logger.info(
            f"Curva por agente - query params: codigos={all_agente_codigos}, fecha_desde={params.get('fecha_desde')}, fecha_hasta={params.get('fecha_hasta')}"
        )
        logger.info(
            f"Curva por agente - {len(rows)} filas, {len(all_agente_codigos)} agentes"
        )

        if not rows:
            return {
                "type": "line",
                "data": {"labels": [], "datasets": [], "metadata": []},
            }

        # Construir estructura de datos
        periodos_set = set()
        datos_por_agente = {}

        for row in rows:
            semana, anio, agente_codigo, casos = row
            periodos_set.add((int(semana), int(anio)))

            if agente_codigo not in datos_por_agente:
                datos_por_agente[agente_codigo] = {}
            datos_por_agente[agente_codigo][(int(semana), int(anio))] = casos

        # Ordenar períodos y generar labels
        periodos_ordenados = sorted(periodos_set, key=lambda x: (x[1], x[0]))
        labels = [f"SE {p[0]}/{p[1]}" for p in periodos_ordenados]

        # Generar metadata
        metadata = []
        for semana, anio in periodos_ordenados:
            try:
                start_date, end_date = obtener_fechas_semana_epidemiologica(
                    anio, semana
                )
                metadata.append(
                    {
                        "year": anio,
                        "week": semana,
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d"),
                    }
                )
            except Exception:
                continue

        # Construir datasets para cada serie
        # NOTA: Ahora cada serie puede tener múltiples agente_codigos que se SUMAN
        datasets = []
        for serie in series_config:
            serie_codigos = serie.get("agente_codigos", [])
            label = serie.get("label", "Serie")
            color = serie.get("color", "rgb(75, 192, 192)")

            # SUMAR datos de todos los agente_codigos en esta serie
            data = []
            for periodo in periodos_ordenados:
                total_periodo = 0
                for agente_codigo in serie_codigos:
                    datos_agente = datos_por_agente.get(agente_codigo, {})
                    total_periodo += datos_agente.get(periodo, 0)
                data.append(total_periodo)

            datasets.append(
                {
                    "label": label,
                    "data": data,
                    "borderColor": color,
                    "backgroundColor": color,
                    "tension": 0.1,
                    "fill": False,
                }
            )

        return {
            "type": "line",
            "data": {"labels": labels, "datasets": datasets, "metadata": metadata},
        }

    async def procesar_corredor_endemico(
        self, filtros: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Procesa datos para corredor endémico
        Calcula percentiles basados en datos históricos (últimos 5 años)
        Muestra solo las semanas del rango de fechas seleccionado
        """

        # Determinar rango de semanas a mostrar basado en filtros de fecha
        fecha_desde = (
            self._parsear_fecha(filtros.get("fecha_desde"))
            if filtros.get("fecha_desde")
            else None
        )
        fecha_hasta = (
            self._parsear_fecha(filtros.get("fecha_hasta"))
            if filtros.get("fecha_hasta")
            else None
        )

        if not fecha_desde or not fecha_hasta:
            return {
                "type": "area",
                "data": {"labels": [], "datasets": [], "metadata": []},
                "error": {
                    "code": "NO_DATE_RANGE",
                    "title": "Rango de fechas requerido",
                    "message": "Seleccione un período de tiempo para visualizar el corredor endémico.",
                    "suggestion": "Configure las fechas desde y hasta en los filtros.",
                },
            }

        # Calcular semanas epidemiológicas del rango
        semana_inicio, año_inicio = calcular_semana_epidemiologica(fecha_desde)
        semana_fin, año_fin = calcular_semana_epidemiologica(fecha_hasta)

        logger.info(
            f"Corredor endémico - Rango: SE {semana_inicio}/{año_inicio} - SE {semana_fin}/{año_fin}"
        )

        # Query para obtener datos históricos (últimos 5 años antes del rango)
        # Generar lista de semanas del rango seleccionado
        weeks_in_range = []
        if semana_inicio is None or semana_fin is None:
            weeks_in_range = []
        elif año_inicio == año_fin:
            # Mismo año
            weeks_in_range = list(range(semana_inicio, semana_fin + 1))
        else:
            # Múltiples años - para simplificar, mostrar todas las semanas
            weeks_in_range = list(range(1, 53))

        # 1. Obtener casos actuales (SIEMPRE se muestran, independiente del histórico)
        current_query = """
        SELECT
            fecha_minima_caso_semana_epi as semana,
            COUNT(*) as casos
        FROM caso_epidemiologico
        WHERE fecha_minima_caso >= :fecha_desde
            AND fecha_minima_caso <= :fecha_hasta
        """

        current_params = {"fecha_desde": fecha_desde, "fecha_hasta": fecha_hasta}

        if filtros.get("grupo_id"):
            current_query += """
                AND id_enfermedad IN (
                    SELECT id_enfermedad FROM enfermedad_grupo WHERE id_grupo = :grupo_id
                )
            """
            current_params["grupo_id"] = filtros["grupo_id"]

        if filtros.get("tipo_eno_ids"):
            tipo_eno_ids = filtros["tipo_eno_ids"]
            if tipo_eno_ids and len(tipo_eno_ids) > 0:
                current_query += " AND id_enfermedad = ANY(:tipo_eno_ids)"
                current_params["tipo_eno_ids"] = tipo_eno_ids

        # Filtro por clasificación estrategia (para datos actuales)
        current_query = self._agregar_filtro_clasificacion(
            current_query, filtros, current_params
        )

        current_query += " GROUP BY semana ORDER BY semana"

        current_result = await self.db.execute(text(current_query), current_params)
        current_rows = current_result.fetchall()

        current_df = (
            pd.DataFrame(current_rows, columns=pd.Index(["semana", "casos"]))
            if current_rows
            else pd.DataFrame()
        )

        # Merge casos actuales con las semanas del rango
        weeks_df = pd.DataFrame({"semana": weeks_in_range})
        if not current_df.empty:
            current_data = weeks_df.merge(current_df, on="semana", how="left").fillna(0)
            casos_actuales = current_data["casos"].tolist()
        else:
            casos_actuales = [0] * len(weeks_in_range)

        # 2. Obtener datos históricos (excluyendo 2020 y 2021)
        query = """
        SELECT
            fecha_minima_caso_semana_epi as semana,
            fecha_minima_caso_anio_epi as año,
            COUNT(*) as casos
        FROM caso_epidemiologico e
        WHERE fecha_minima_caso >= :fecha_historica_inicio
            AND fecha_minima_caso < :fecha_desde
            AND fecha_minima_caso_anio_epi NOT IN (2020, 2021) -- Excluir años pandemicos anómalos
        """

        params = {
            "fecha_desde": fecha_desde,
            "fecha_historica_inicio": date(fecha_desde.year - 5, 1, 1),  # 5 años atrás
        }

        if filtros.get("grupo_id"):
            query += """
                AND e.id_enfermedad IN (
                    SELECT id_enfermedad FROM enfermedad_grupo WHERE id_grupo = :grupo_id
                )
            """
            params["grupo_id"] = filtros["grupo_id"]

        if filtros.get("tipo_eno_ids"):
            tipo_eno_ids = filtros["tipo_eno_ids"]
            if tipo_eno_ids and len(tipo_eno_ids) > 0:
                query += " AND e.id_enfermedad = ANY(:tipo_eno_ids)"
                params["tipo_eno_ids"] = tipo_eno_ids

        # Filtro por clasificación estrategia (para histórico)
        query = self._agregar_filtro_clasificacion(query, filtros, params, "e")

        query += " GROUP BY semana, año ORDER BY semana, año"

        result = await self.db.execute(text(query), params)
        rows = result.fetchall()

        # 3. Validar datos históricos y Calcular Percentiles
        warnings = []
        corredor_valido = False
        percentiles = pd.DataFrame()

        if not rows or len(rows) < 10:
            warnings.append(
                "Datos históricos insuficientes para calcular zonas (se requieren min 2 años previos excluyendo 2020-2021)."
            )
        else:
            df = pd.DataFrame(rows, columns=pd.Index(["semana", "año", "casos"]))

            # Validar años únicos (Mínimo 2 años requeridos, bajado de 3)
            años_unicos = df["año"].nunique()
            años_lista = sorted(df["año"].unique().tolist())

            if años_unicos < 2:
                warnings.append(
                    f"Se requieren min 2 años de historia (excl. 2020-2021). Disponibles: {años_unicos} ({', '.join(map(str, años_lista))})."
                )
            else:
                corredor_valido = True
                # Calcular percentiles solo para las semanas en el rango
                percentiles = (
                    df.groupby("semana")["casos"]
                    .agg(
                        [
                            ("minimo", lambda x: x.quantile(0.25)),
                            ("mediana", lambda x: x.quantile(0.5)),
                            ("maximo", lambda x: x.quantile(0.75)),
                        ]
                    )
                    .reset_index()
                )

        # Preparar DataFrame de zonas (lleno con 0 si no es válido)
        if corredor_valido and not percentiles.empty:
            percentiles_merged = weeks_df.merge(
                percentiles, on="semana", how="left"
            ).fillna(0)
        else:
            # Crear dataframe con ceros
            percentiles_merged = pd.DataFrame(
                {"semana": weeks_in_range, "minimo": 0, "mediana": 0, "maximo": 0}
            )

        # Generar metadata para las semanas del rango
        metadata = []
        for week in weeks_in_range:
            # Initialize year_for_week before try block
            year_for_week = (
                int(año_inicio if año_inicio == año_fin else año_fin)
                if año_inicio is not None and año_fin is not None
                else datetime.now().year
            )
            try:
                # Usar año correspondiente (año_inicio para simplificar, o año_fin si es multi-año)
                start_date, end_date = obtener_fechas_semana_epidemiologica(
                    year_for_week, int(week)
                )
                metadata.append(
                    {
                        "year": year_for_week,
                        "week": week,
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d"),
                    }
                )
            except Exception as e:
                logger.warning(
                    f"Error generando metadata para semana {week}/{year_for_week}: {e}"
                )
                continue

        # Generar labels
        year_label = año_inicio if año_inicio == año_fin else f"{año_inicio}-{año_fin}"
        labels = [f"SE {int(week)}/{year_label}" for week in weeks_in_range]

        return {
            "type": "area",
            "metadata": {
                "warnings": warnings,
                "years_found": años_lista if "años_lista" in locals() else [],  # type: ignore[possibly-unresolved-reference]
            },
            "data": {
                "labels": labels,
                "datasets": [
                    {
                        "label": "Máximo (P75)",
                        "data": percentiles_merged["maximo"].tolist(),
                        "color": "rgba(255, 0, 0, 0.8)",
                    },
                    {
                        "label": "Mediana (P50)",
                        "data": percentiles_merged["mediana"].tolist(),
                        "color": "rgba(255, 165, 0, 0.8)",
                    },
                    {
                        "label": "Mínimo (P25)",
                        "data": percentiles_merged["minimo"].tolist(),
                        "color": "rgba(0, 255, 0, 0.8)",
                    },
                    {
                        "label": "Casos actuales",
                        "data": casos_actuales,
                        "color": "rgba(59, 130, 246, 1)",  # Blue-500 sólido
                        "type": "line",
                    },
                ],
                "metadata": metadata,
            },
        }

    async def procesar_piramide_poblacional(
        self, filtros: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Procesa datos para pirámide poblacional - Solo Chubut
        Usa configuración flexible de grupos etarios desde age_groups_config.py

        Parámetros de filtros opcionales:
            - age_group_config: str = "standard" | "pediatric" | "simple" | "decennial"
        """
        # Obtener configuración de grupos etarios
        age_group_config_name = filtros.get("age_group_config", "standard")
        age_groups_config = obtener_configuracion_grupos_edad(age_group_config_name)
        age_group_labels = obtener_etiquetas_grupos_edad(age_groups_config)

        # Generar CASE WHEN dinámico basado en la configuración
        case_when_sql = generar_sql_case_when(age_groups_config)

        # Query para obtener distribución por edad y sexo
        # Usa sexo_biologico_al_nacer si existe, sino sexo_biologico
        query = f"""
        SELECT
            {case_when_sql} as grupo_edad,
            COALESCE(c.sexo_biologico, c.sexo_biologico_al_nacer, 'NO_ESPECIFICADO') as sexo,
            COUNT(*) as casos
        FROM caso_epidemiologico e
        LEFT JOIN ciudadano c ON e.codigo_ciudadano = c.codigo_ciudadano
        LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
        LEFT JOIN localidad l ON est.id_localidad_indec = l.id_localidad_indec
        LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
        WHERE e.fecha_nacimiento IS NOT NULL
          AND e.fecha_minima_caso IS NOT NULL
        """

        params = {}

        # Filtro de provincia
        query, params = self._agregar_filtro_provincia(query, filtros, params, "d")

        if filtros.get("grupo_id"):
            query += """
                AND e.id_enfermedad IN (
                    SELECT id_enfermedad FROM enfermedad_grupo WHERE id_grupo = :grupo_id
                )
            """
            params["grupo_id"] = filtros["grupo_id"]

        if filtros.get("tipo_eno_ids"):
            tipo_eno_ids = filtros["tipo_eno_ids"]
            if tipo_eno_ids and len(tipo_eno_ids) > 0:
                query += " AND e.id_enfermedad = ANY(:tipo_eno_ids)"
                params["tipo_eno_ids"] = tipo_eno_ids

        # Filtro por clasificación estrategia
        query = self._agregar_filtro_clasificacion(query, filtros, params, "e")

        # CRÍTICO: Agregar filtros de fecha
        if filtros.get("fecha_desde"):
            query += " AND e.fecha_minima_caso >= :fecha_desde"
            params["fecha_desde"] = self._parsear_fecha(filtros["fecha_desde"])

        if filtros.get("fecha_hasta"):
            query += " AND e.fecha_minima_caso <= :fecha_hasta"
            params["fecha_hasta"] = self._parsear_fecha(filtros["fecha_hasta"])

        query += " GROUP BY grupo_edad, sexo ORDER BY grupo_edad"

        result = await self.db.execute(text(query), params)
        rows = result.fetchall()

        logger.info(
            f"🔍 Pirámide poblacional ({age_group_config_name}) - Filas encontradas: {len(rows)}"
        )
        if rows and len(rows) > 0:
            logger.info(f"📊 Pirámide poblacional - Primeras 5 filas: {rows[:5]}")
            logger.info(
                f"👥 Pirámide poblacional - Valores de sexo encontrados: { {row[1] for row in rows} }"
            )

        # Procesar para formato de pirámide usando los labels de la configuración
        male_data = dict.fromkeys(age_group_labels, 0)
        female_data = dict.fromkeys(age_group_labels, 0)

        for row in rows:
            grupo_edad, sexo, casos = row

            # Ignorar grupo "Desconocido" si existe
            if grupo_edad == "Desconocido":
                continue

            # Solo procesar datos con sexo especificado
            if sexo == "MASCULINO":
                if grupo_edad in male_data:
                    male_data[grupo_edad] = casos
            elif sexo == "FEMENINO" and grupo_edad in female_data:
                female_data[grupo_edad] = casos
            # Ignorar casos con sexo NO_ESPECIFICADO - no crear datos falsos

        # Preparar datos para D3.js - formato de pirámide poblacional
        # Incluir todos los grupos de edad, incluso con 0 casos
        pyramid_data = []
        for age_group in age_group_labels:
            male_count = male_data[age_group]
            female_count = female_data[age_group]

            # Agregar entrada para masculino y femenino
            pyramid_data.append(
                {
                    "age_group": age_group,
                    "male": male_count,
                    "female": female_count,
                }
            )

        total_male = sum(male_data.values())
        total_female = sum(female_data.values())

        logger.info(
            f"✅ Pirámide poblacional - Total M: {total_male}, F: {total_female}"
        )

        return {
            "type": "d3_pyramid",
            "data": pyramid_data,
            "metadata": {
                "age_groups": age_group_labels,
                "age_group_config": age_group_config_name,
                "total_male": total_male,
                "total_female": total_female,
                "total_casos": total_male + total_female,
            },
        }

    async def procesar_mapa_geografico(self, filtros: dict[str, Any]) -> dict[str, Any]:
        """
        Procesa datos para mapa geográfico con departamentos de Chubut
        """
        from datetime import datetime

        from app.core.static_data.geografia_chubut import (
            DEPARTAMENTOS_CHUBUT,
            POBLACION_DEPARTAMENTOS,
            get_zona_ugd,
        )

        # Query para obtener casos por departamento
        query = """
        SELECT
            COALESCE(d.id_departamento_indec, 0) as codigo_indec,
            COUNT(DISTINCT e.id) as casos
        FROM caso_epidemiologico e
        LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
        LEFT JOIN localidad l ON est.id_localidad_indec = l.id_localidad_indec
        LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
        WHERE 1=1
        """

        params = {}

        # Filtro de provincia
        query, params = self._agregar_filtro_provincia(query, filtros, params, "d")

        if filtros.get("grupo_id"):
            query += """
                AND e.id_enfermedad IN (
                    SELECT id_enfermedad FROM enfermedad_grupo WHERE id_grupo = :grupo_id
                )
            """
            params["grupo_id"] = filtros["grupo_id"]

        if filtros.get("tipo_eno_ids"):
            tipo_eno_ids = filtros["tipo_eno_ids"]
            if tipo_eno_ids and len(tipo_eno_ids) > 0:
                query += " AND e.id_enfermedad = ANY(:tipo_eno_ids)"
                params["tipo_eno_ids"] = tipo_eno_ids

        # Filtro por clasificación estrategia
        query = self._agregar_filtro_clasificacion(query, filtros, params, "e")

        if filtros.get("fecha_desde"):
            query += " AND e.fecha_minima_caso >= :fecha_desde"
            # Convert string to date if necessary
            fecha_desde = filtros["fecha_desde"]
            if isinstance(fecha_desde, str):
                fecha_desde = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
            params["fecha_desde"] = fecha_desde

        if filtros.get("fecha_hasta"):
            query += " AND e.fecha_minima_caso <= :fecha_hasta"
            # Convert string to date if necessary
            fecha_hasta = filtros["fecha_hasta"]
            if isinstance(fecha_hasta, str):
                fecha_hasta = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
            params["fecha_hasta"] = fecha_hasta

        query += " GROUP BY d.id_departamento_indec"

        result = await self.db.execute(text(query), params)
        rows = result.fetchall()

        # Crear mapa de casos por departamento
        casos_por_departamento = {
            row.codigo_indec: row.casos for row in rows if row.codigo_indec
        }

        # Construir datos para todos los departamentos
        departamentos_data = []
        for codigo_indec in DEPARTAMENTOS_CHUBUT:
            casos = casos_por_departamento.get(codigo_indec, 0)
            poblacion = POBLACION_DEPARTAMENTOS.get(codigo_indec, 0)
            tasa_incidencia = (
                round((casos / poblacion) * 100000, 2) if poblacion > 0 else 0.0
            )

            departamentos_data.append(
                {
                    "codigo_indec": codigo_indec,
                    "nombre": DEPARTAMENTOS_CHUBUT[codigo_indec],
                    "zona_ugd": get_zona_ugd(codigo_indec),
                    "poblacion": poblacion,
                    "casos": casos,
                    "tasa_incidencia": tasa_incidencia,
                }
            )

        total_casos = sum(casos_por_departamento.values())
        logger.info(
            f"Mapa geográfico - Departamentos con casos: {len(casos_por_departamento)}"
        )
        logger.info(f"📊 Mapa geográfico - TOTAL CASOS: {total_casos}")

        return {
            "type": "mapa",
            "data": {"departamentos": departamentos_data, "total_casos": total_casos},
        }

    async def procesar_estacionalidad(self, filtros: dict[str, Any]) -> dict[str, Any]:
        """
        Procesa datos para estacionalidad mensual - Solo Chubut
        Muestra la distribución de casos por mes del año
        """
        query = """
        SELECT
            EXTRACT(MONTH FROM e.fecha_minima_caso) as mes,
            COUNT(*) as casos
        FROM caso_epidemiologico e
        LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
        LEFT JOIN localidad l ON est.id_localidad_indec = l.id_localidad_indec
        LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
        WHERE e.fecha_minima_caso IS NOT NULL
        """

        params = {}

        # Filtro de provincia (Chubut si está activado)
        query, params = self._agregar_filtro_provincia(query, filtros, params, "d")

        if filtros.get("grupo_id"):
            query += """
                AND e.id_enfermedad IN (
                    SELECT id_enfermedad FROM enfermedad_grupo WHERE id_grupo = :grupo_id
                )
            """
            params["grupo_id"] = filtros["grupo_id"]

        if filtros.get("tipo_eno_ids"):
            tipo_eno_ids = filtros["tipo_eno_ids"]
            if tipo_eno_ids and len(tipo_eno_ids) > 0:
                query += " AND e.id_enfermedad = ANY(:tipo_eno_ids)"
                params["tipo_eno_ids"] = tipo_eno_ids

        # Filtro por clasificación estrategia
        query = self._agregar_filtro_clasificacion(query, filtros, params, "e")

        # Filtros de fecha
        if filtros.get("fecha_desde"):
            query += " AND e.fecha_minima_caso >= :fecha_desde"
            params["fecha_desde"] = self._parsear_fecha(filtros["fecha_desde"])

        if filtros.get("fecha_hasta"):
            query += " AND e.fecha_minima_caso <= :fecha_hasta"
            params["fecha_hasta"] = self._parsear_fecha(filtros["fecha_hasta"])

        query += " GROUP BY mes ORDER BY mes"

        result = await self.db.execute(text(query), params)
        rows = result.fetchall()

        logger.info(f"Estacionalidad - Filas encontradas: {len(rows)}")

        # Nombres de meses en español
        meses_nombres = [
            "Enero",
            "Febrero",
            "Marzo",
            "Abril",
            "Mayo",
            "Junio",
            "Julio",
            "Agosto",
            "Septiembre",
            "Octubre",
            "Noviembre",
            "Diciembre",
        ]

        # Crear diccionario con todos los meses (inicializar en 0)
        casos_por_mes = dict.fromkeys(range(1, 13), 0)

        # Llenar con los datos obtenidos
        for row in rows:
            mes = int(row[0]) if row[0] else 0
            if 1 <= mes <= 12:
                casos_por_mes[mes] = row[1]

        # Formato nuevo: BaseChartData compatible
        return {
            "data": {
                "labels": meses_nombres,
                "datasets": [
                    {
                        "label": "Casos",
                        "data": [int(casos_por_mes[i]) for i in range(1, 13)],
                        "backgroundColor": "rgba(54, 162, 235, 0.5)",
                    }
                ],
            }
        }

    async def procesar_casos_edad(
        self,
        filtros: dict[str, Any],
        series_config: list[dict[str, Any]] | None = None,
        agrupar_por: str | None = None,
    ) -> dict[str, Any]:
        """
        Procesa datos para casos por grupos de edad con soporte para múltiples series.

        Args:
            filtros: Filtros base
            series_config: Lista de configuraciones de serie. Cada serie tiene:
                - tipo_eno_id: ID del tipo_eno (para agrupar por evento)
                - agente_codigo: Código del agente (para agrupar por agente)
                - label: Etiqueta para la leyenda
                - color: Color de la barra
            agrupar_por: "evento" | "agente" | None
        """
        # Si agrupamos por agente, usar procesamiento especial
        if agrupar_por == "agente" and series_config:
            return await self._procesar_casos_edad_por_agente(filtros, series_config)

        # Si agrupamos por evento (múltiples series), procesar con series
        if agrupar_por == "evento" and series_config:
            return await self._procesar_casos_edad_por_evento(filtros, series_config)

        # Procesamiento simple (una sola serie)
        query = """
        SELECT
            CASE
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 1 THEN '< 1 año'
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 5 THEN '1-4'
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 10 THEN '5-9'
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 15 THEN '10-14'
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 20 THEN '15-19'
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 30 THEN '20-29'
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 40 THEN '30-39'
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 50 THEN '40-49'
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 60 THEN '50-59'
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 70 THEN '60-69'
                ELSE '70+'
            END as grupo_edad,
            COUNT(*) as casos
        FROM caso_epidemiologico e
        """

        params = {}

        # Lazy Joins: Solo hacer JOINs geográficos si hay filtro de provincia
        if filtros.get("provincia_id"):
            query += """
            LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
            LEFT JOIN localidad l ON est.id_localidad_indec = l.id_localidad_indec
            LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
            """

        query += """
        WHERE e.fecha_nacimiento IS NOT NULL
          AND e.fecha_minima_caso IS NOT NULL
        """

        params = {}

        # Filtro de provincia (Chubut si está activado)
        query, params = self._agregar_filtro_provincia(query, filtros, params, "d")

        if filtros.get("grupo_id"):
            query += """
                AND e.id_enfermedad IN (
                    SELECT id_enfermedad FROM enfermedad_grupo WHERE id_grupo = :grupo_id
                )
            """
            params["grupo_id"] = filtros["grupo_id"]

        if filtros.get("tipo_eno_ids"):
            tipo_eno_ids = filtros["tipo_eno_ids"]
            if tipo_eno_ids and len(tipo_eno_ids) > 0:
                query += " AND e.id_enfermedad = ANY(:tipo_eno_ids)"
                params["tipo_eno_ids"] = tipo_eno_ids

        # Filtro por clasificación estrategia
        query = self._agregar_filtro_clasificacion(query, filtros, params, "e")

        # CRÍTICO: Agregar filtros de fecha
        if filtros.get("fecha_desde"):
            query += " AND e.fecha_minima_caso >= :fecha_desde"
            params["fecha_desde"] = self._parsear_fecha(filtros["fecha_desde"])

        if filtros.get("fecha_hasta"):
            query += " AND e.fecha_minima_caso <= :fecha_hasta"
            params["fecha_hasta"] = self._parsear_fecha(filtros["fecha_hasta"])

        query += " GROUP BY grupo_edad ORDER BY MIN(EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)))"

        result = await self.db.execute(text(query), params)
        rows = result.fetchall()

        logger.info(f"Casos por edad - Filas encontradas: {len(rows)}")
        if rows and len(rows) > 0:
            logger.info(f"Casos por edad - Grupos: {rows}")

        # Formato nuevo: BaseChartData compatible
        labels = [str(row[0]) for row in rows] if rows else []
        data_values = [int(row[1]) for row in rows] if rows else []

        return {
            "data": {
                "labels": labels,
                "datasets": [
                    {
                        "label": "Casos",
                        "data": data_values,
                        "backgroundColor": "rgba(153, 102, 255, 0.5)",
                    }
                ],
            }
        }

    async def _procesar_casos_edad_por_evento(
        self, filtros: dict[str, Any], series_config: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Procesa distribución por edad agrupada por múltiples eventos (tipo_eno).
        Cada serie puede agrupar múltiples tipo_eno_ids que se suman.

        Args:
            filtros: Filtros base
            series_config: Lista de configuraciones. Cada serie tiene:
                - tipo_eno_ids: Array de IDs de tipo_eno (se SUMAN para esta serie)
                - label: Etiqueta para la leyenda
                - color: Color de la barra
        """
        # Extraer TODOS los IDs de todas las series (aplanar arrays)
        all_tipo_eno_ids = []
        for serie in series_config:
            all_tipo_eno_ids.extend(serie.get("tipo_eno_ids", []))

        # Eliminar duplicados manteniendo orden
        all_tipo_eno_ids = list(dict.fromkeys(all_tipo_eno_ids))

        if not all_tipo_eno_ids:
            return {
                "data": {"labels": [], "datasets": []},
                "error": "No se configuraron eventos para el gráfico",
            }

        # Query agrupada por tipo_eno y grupo etario
        query = """
        SELECT
            CASE
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 1 THEN '< 1 año'
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 5 THEN '1-4'
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 10 THEN '5-9'
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 15 THEN '10-14'
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 20 THEN '15-19'
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 30 THEN '20-29'
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 40 THEN '30-39'
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 50 THEN '40-49'
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 60 THEN '50-59'
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 70 THEN '60-69'
                ELSE '70+'
            END as grupo_edad,
            e.id_enfermedad,
            COUNT(*) as casos
        FROM caso_epidemiologico e
        WHERE e.fecha_nacimiento IS NOT NULL
          AND e.fecha_minima_caso IS NOT NULL
          AND e.id_enfermedad = ANY(:tipo_eno_ids)
        """

        params: dict[str, Any] = {"tipo_eno_ids": all_tipo_eno_ids}

        if filtros.get("fecha_desde"):
            query += " AND e.fecha_minima_caso >= :fecha_desde"
            params["fecha_desde"] = self._parsear_fecha(filtros["fecha_desde"])

        if filtros.get("fecha_hasta"):
            query += " AND e.fecha_minima_caso <= :fecha_hasta"
            params["fecha_hasta"] = self._parsear_fecha(filtros["fecha_hasta"])

        query += " GROUP BY grupo_edad, e.id_enfermedad ORDER BY MIN(EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento))), e.id_enfermedad"

        result = await self.db.execute(text(query), params)
        rows = result.fetchall()

        logger.info(
            f"Casos por edad por evento - {len(rows)} filas, {len(all_tipo_eno_ids)} eventos"
        )

        # Grupos etarios ordenados
        grupos_etarios = [
            "< 1 año",
            "1-4",
            "5-9",
            "10-14",
            "15-19",
            "20-29",
            "30-39",
            "40-49",
            "50-59",
            "60-69",
            "70+",
        ]

        # Organizar datos por tipo_eno y grupo etario
        datos_por_tipo = {}
        for row in rows:
            grupo_edad, tipo_eno_id, casos = row
            if tipo_eno_id not in datos_por_tipo:
                datos_por_tipo[tipo_eno_id] = {}
            datos_por_tipo[tipo_eno_id][grupo_edad] = casos

        # Construir datasets para cada serie
        # NOTA: Ahora cada serie puede tener múltiples tipo_eno_ids que se SUMAN
        datasets = []
        for serie in series_config:
            serie_ids = serie.get("tipo_eno_ids", [])
            label = serie.get("label", "Serie")
            color = serie.get("color", "#4CAF50")

            # SUMAR datos de todos los tipo_eno_ids en esta serie para cada grupo etario
            data = []
            for grupo in grupos_etarios:
                total_grupo = 0
                for tipo_eno_id in serie_ids:
                    datos_tipo = datos_por_tipo.get(tipo_eno_id, {})
                    total_grupo += datos_tipo.get(grupo, 0)
                data.append(total_grupo)

            datasets.append(
                {
                    "label": label,
                    "data": data,
                    "backgroundColor": color,
                    "color": color,  # También agregamos color para compatibilidad
                }
            )

        logger.info(
            f"_procesar_casos_edad_por_evento: {len(datasets)} series - {[(d['label'], d['color']) for d in datasets]}"
        )

        return {"data": {"labels": grupos_etarios, "datasets": datasets}}

    async def _procesar_casos_edad_por_agente(
        self, filtros: dict[str, Any], series_config: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Procesa distribución por edad agrupada por agentes etiológicos.
        Cada serie puede agrupar múltiples agente_codigos que se suman.

        Args:
            filtros: Filtros base
            series_config: Lista de configuraciones. Cada serie tiene:
                - agente_codigos: Array de códigos de agente (se SUMAN para esta serie)
                - label: Etiqueta para la leyenda
                - color: Color de la barra
        """
        # Extraer TODOS los códigos de agentes de todas las series (aplanar arrays)
        all_agente_codigos = []
        for serie in series_config:
            all_agente_codigos.extend(serie.get("agente_codigos", []))

        # Eliminar duplicados manteniendo orden
        all_agente_codigos = list(dict.fromkeys(all_agente_codigos))

        if not all_agente_codigos:
            return {
                "data": {"labels": [], "datasets": []},
                "error": "No se configuraron agentes para el gráfico",
            }

        # Query agrupada por agente y grupo etario
        query = """
        SELECT
            CASE
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 1 THEN '< 1 año'
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 5 THEN '1-4'
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 10 THEN '5-9'
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 15 THEN '10-14'
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 20 THEN '15-19'
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 30 THEN '20-29'
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 40 THEN '30-39'
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 50 THEN '40-49'
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 60 THEN '50-59'
                WHEN EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento)) < 70 THEN '60-69'
                ELSE '70+'
            END as grupo_edad,
            ae.slug as agente_codigo,
            COUNT(DISTINCT e.id) as casos
        FROM caso_epidemiologico e
        JOIN caso_agente ea ON e.id = ea.id_caso
        JOIN agente_etiologico ae ON ea.id_agente = ae.id
        WHERE e.fecha_nacimiento IS NOT NULL
          AND ae.slug = ANY(:agente_codigos)
          AND ea.resultado = :resultado_positivo
        """

        params: dict[str, Any] = {
            "agente_codigos": all_agente_codigos,
            "resultado_positivo": ResultadoDeteccion.POSITIVO.value,
        }

        if filtros.get("fecha_desde"):
            query += " AND e.fecha_minima_caso >= :fecha_desde"
            params["fecha_desde"] = self._parsear_fecha(filtros["fecha_desde"])

        if filtros.get("fecha_hasta"):
            query += " AND e.fecha_minima_caso <= :fecha_hasta"
            params["fecha_hasta"] = self._parsear_fecha(filtros["fecha_hasta"])

        query += " GROUP BY grupo_edad, agente_codigo ORDER BY MIN(EXTRACT(YEAR FROM AGE(e.fecha_minima_caso, e.fecha_nacimiento))), agente_codigo"

        result = await self.db.execute(text(query), params)
        rows = result.fetchall()

        logger.info(
            f"Casos por edad por agente - {len(rows)} filas, {len(all_agente_codigos)} agentes"
        )

        # Grupos etarios ordenados
        grupos_etarios = [
            "< 1 año",
            "1-4",
            "5-9",
            "10-14",
            "15-19",
            "20-29",
            "30-39",
            "40-49",
            "50-59",
            "60-69",
            "70+",
        ]

        # Organizar datos por agente y grupo etario
        datos_por_agente = {}
        for row in rows:
            grupo_edad, agente_codigo, casos = row
            if agente_codigo not in datos_por_agente:
                datos_por_agente[agente_codigo] = {}
            datos_por_agente[agente_codigo][grupo_edad] = casos

        # Construir datasets para cada serie
        # NOTA: Ahora cada serie puede tener múltiples agente_codigos que se SUMAN
        datasets = []
        for serie in series_config:
            serie_codigos = serie.get("agente_codigos", [])
            label = serie.get("label", "Serie")
            color = serie.get("color", "#2196F3")

            # SUMAR datos de todos los agente_codigos en esta serie para cada grupo etario
            data = []
            for grupo in grupos_etarios:
                total_grupo = 0
                for agente_codigo in serie_codigos:
                    datos_agente = datos_por_agente.get(agente_codigo, {})
                    total_grupo += datos_agente.get(grupo, 0)
                data.append(total_grupo)

            datasets.append(
                {
                    "label": label,
                    "data": data,
                    "backgroundColor": color,
                }
            )

        return {"data": {"labels": grupos_etarios, "datasets": datasets}}

    async def procesar_intento_suicidio(
        self, filtros: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Procesa datos específicos para intentos de suicidio
        Similar al sistema Chubut pero con datos reales
        """
        # Este chart solo se muestra para eventos de salud mental
        # Por ahora retorna estructura vacía hasta tener datos específicos
        query = """
        SELECT
            'Método' as categoria,
            COUNT(*) as casos
        FROM caso_epidemiologico e
        WHERE e.id_enfermedad IN (
            SELECT id FROM enfermedad WHERE LOWER(nombre) LIKE '%suicid%'
        )
        """

        params = {}

        if filtros.get("tipo_eno_ids"):
            tipo_eno_ids = filtros["tipo_eno_ids"]
            if tipo_eno_ids and len(tipo_eno_ids) > 0:
                query += " AND e.id_enfermedad = ANY(:tipo_eno_ids)"
                params["tipo_eno_ids"] = tipo_eno_ids

        # CRÍTICO: Agregar filtros de fecha
        if filtros.get("fecha_desde"):
            query += " AND e.fecha_minima_caso >= :fecha_desde"
            params["fecha_desde"] = self._parsear_fecha(filtros["fecha_desde"])

        if filtros.get("fecha_hasta"):
            query += " AND e.fecha_minima_caso <= :fecha_hasta"
            params["fecha_hasta"] = self._parsear_fecha(filtros["fecha_hasta"])

        query += " GROUP BY categoria"

        result = await self.db.execute(text(query), params)
        rows = result.fetchall()

        if not rows:
            return {
                "type": "bar",
                "data": {
                    "labels": [],
                    "datasets": [{"label": "Casos", "data": [], "backgroundColor": []}],
                },
            }

        # TODO: Implementar categorización específica cuando tengamos campos de método
        return {
            "type": "bar",
            "data": {
                "labels": ["Total registrado"],
                "datasets": [
                    {
                        "label": "Casos",
                        "data": [rows[0][1] if rows else 0],
                        "backgroundColor": ["rgba(255, 99, 132, 0.5)"],
                    }
                ],
            },
        }

    async def procesar_rabia_animal(self, filtros: dict[str, Any]) -> dict[str, Any]:
        """
        Procesa datos específicos para rabia animal
        """
        # Similar al anterior, específico para zoonosis
        query = """
        SELECT
            COALESCE(a.especie, 'No especificado') as especie,
            COUNT(*) as casos
        FROM caso_epidemiologico e
        LEFT JOIN animal a ON e.id_animal = a.id
        WHERE e.id_enfermedad IN (
            SELECT id FROM enfermedad WHERE LOWER(nombre) LIKE '%rabia%'
        )
        """

        params = {}

        if filtros.get("tipo_eno_ids"):
            tipo_eno_ids = filtros["tipo_eno_ids"]
            if tipo_eno_ids and len(tipo_eno_ids) > 0:
                query += " AND e.id_enfermedad = ANY(:tipo_eno_ids)"
                params["tipo_eno_ids"] = tipo_eno_ids

        # CRÍTICO: Agregar filtros de fecha
        if filtros.get("fecha_desde"):
            query += " AND e.fecha_minima_caso >= :fecha_desde"
            params["fecha_desde"] = self._parsear_fecha(filtros["fecha_desde"])

        if filtros.get("fecha_hasta"):
            query += " AND e.fecha_minima_caso <= :fecha_hasta"
            params["fecha_hasta"] = self._parsear_fecha(filtros["fecha_hasta"])

        query += " GROUP BY especie"

        result = await self.db.execute(text(query), params)
        rows = result.fetchall()

        if not rows:
            return {
                "type": "bar",
                "data": {
                    "labels": [],
                    "datasets": [
                        {
                            "label": "Casos por especie",
                            "data": [],
                            "backgroundColor": [],
                        }
                    ],
                },
            }

        return {
            "type": "bar",
            "data": {
                "labels": [row[0] for row in rows],
                "datasets": [
                    {
                        "label": "Casos por especie",
                        "data": [row[1] for row in rows],
                        "backgroundColor": [
                            "rgba(255, 159, 64, 0.5)",
                            "rgba(153, 102, 255, 0.5)",
                            "rgba(75, 192, 192, 0.5)",
                            "rgba(255, 99, 132, 0.5)",
                        ][: len(rows)],
                    }
                ],
            },
        }

    async def procesar_proporcion_ira(self, filtros: dict[str, Any]) -> dict[str, Any]:
        """
        Procesa datos para proporción de IRA (Infecciones Respiratorias Agudas)
        Basado en unidades centinela
        """
        query = """
        SELECT
            CASE
                WHEN LOWER(t.nombre) LIKE '%ira%' OR LOWER(t.nombre) LIKE '%respiratoria%' THEN 'IRA'
                WHEN LOWER(t.nombre) LIKE '%irag%' OR LOWER(t.nombre) LIKE '%grave%' THEN 'IRAG'
                WHEN LOWER(t.nombre) LIKE '%neumonia%' THEN 'Neumonía'
                WHEN LOWER(t.nombre) LIKE '%bronquiolitis%' THEN 'Bronquiolitis'
                ELSE 'Otras respiratorias'
            END as tipo_respiratorio,
            COUNT(*) as casos
        FROM caso_epidemiologico e
        JOIN enfermedad t ON e.id_enfermedad = t.id
        JOIN enfermedad_grupo tge ON t.id = tge.id_enfermedad
        JOIN grupo_de_enfermedades g ON tge.id_grupo = g.id
        WHERE LOWER(g.nombre) LIKE '%respiratoria%'
           OR LOWER(t.nombre) LIKE '%ira%'
           OR LOWER(t.nombre) LIKE '%respiratoria%'
        """

        params = {}

        if filtros.get("grupo_id"):
            query += " AND tge.id_grupo = :grupo_id"
            params["grupo_id"] = filtros["grupo_id"]

        if filtros.get("tipo_eno_ids"):
            tipo_eno_ids = filtros["tipo_eno_ids"]
            if tipo_eno_ids and len(tipo_eno_ids) > 0:
                query += " AND e.id_enfermedad = ANY(:tipo_eno_ids)"
                params["tipo_eno_ids"] = tipo_eno_ids

        if filtros.get("fecha_desde"):
            query += " AND e.fecha_minima_caso >= :fecha_desde"
            params["fecha_desde"] = self._parsear_fecha(filtros["fecha_desde"])

        if filtros.get("fecha_hasta"):
            query += " AND e.fecha_minima_caso <= :fecha_hasta"
            params["fecha_hasta"] = self._parsear_fecha(filtros["fecha_hasta"])

        query += " GROUP BY tipo_respiratorio ORDER BY casos DESC"

        result = await self.db.execute(text(query), params)
        rows = result.fetchall()

        logger.info(f"Proporción IRA - Filas encontradas: {len(rows)}")
        if rows and len(rows) > 0:
            logger.info(f"Proporción IRA - Tipos: {rows}")

        if not rows:
            return {
                "type": "pie",
                "data": {
                    "labels": ["Sin datos"],
                    "datasets": [
                        {"data": [1], "backgroundColor": ["rgba(200, 200, 200, 0.5)"]}
                    ],
                },
            }

        # Calcular total para proporciones
        total_casos = sum(row[1] for row in rows)

        return {
            "type": "pie",
            "data": {
                "labels": [row[0] for row in rows],
                "datasets": [
                    {
                        "data": [row[1] for row in rows],
                        "backgroundColor": [
                            "rgba(54, 162, 235, 0.7)",  # IRA - Azul
                            "rgba(255, 99, 132, 0.7)",  # IRAG - Rojo
                            "rgba(255, 206, 86, 0.7)",  # Neumonía - Amarillo
                            "rgba(75, 192, 192, 0.7)",  # Bronquiolitis - Verde
                            "rgba(153, 102, 255, 0.7)",  # Otras - Púrpura
                        ][: len(rows)],
                    }
                ],
            },
            "metadata": {
                "total_casos": total_casos,
                "proporciones": [
                    {
                        "tipo": row[0],
                        "casos": row[1],
                        "porcentaje": round((row[1] / total_casos) * 100, 2)
                        if total_casos > 0
                        else 0,
                    }
                    for row in rows
                ],
            },
        }

    async def procesar_distribucion_clasificacion(
        self, filtros: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Procesa datos para distribución por clasificación estratégica - Solo Chubut
        Muestra casos por tipo de clasificación (CONFIRMADOS, PROBABLES, SOSPECHOSOS, etc.)
        """
        query = """
        SELECT
            COALESCE(CAST(e.clasificacion_estrategia AS TEXT), 'SIN_CLASIFICAR') as clasificacion,
            COUNT(DISTINCT e.id) as casos
        FROM caso_epidemiologico e
        LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
        LEFT JOIN localidad l ON est.id_localidad_indec = l.id_localidad_indec
        LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
        WHERE 1=1
        """

        params = {}

        # Filtro de provincia (Chubut si está activado)
        query, params = self._agregar_filtro_provincia(query, filtros, params, "d")

        if filtros.get("grupo_id"):
            query += """
                AND e.id_enfermedad IN (
                    SELECT id_enfermedad FROM enfermedad_grupo WHERE id_grupo = :grupo_id
                )
            """
            params["grupo_id"] = filtros["grupo_id"]

        if filtros.get("tipo_eno_ids"):
            tipo_eno_ids = filtros["tipo_eno_ids"]
            if tipo_eno_ids and len(tipo_eno_ids) > 0:
                query += " AND e.id_enfermedad = ANY(:tipo_eno_ids)"
                params["tipo_eno_ids"] = tipo_eno_ids

        # Filtro por clasificaciones (usar helper consistente)
        query = self._agregar_filtro_clasificacion(
            query, filtros, params, table_alias="e"
        )

        # Filtros de fecha
        if filtros.get("fecha_desde"):
            query += " AND e.fecha_minima_caso >= :fecha_desde"
            params["fecha_desde"] = self._parsear_fecha(filtros["fecha_desde"])

        if filtros.get("fecha_hasta"):
            query += " AND e.fecha_minima_caso <= :fecha_hasta"
            params["fecha_hasta"] = self._parsear_fecha(filtros["fecha_hasta"])

        query += " GROUP BY clasificacion ORDER BY casos DESC"

        result = await self.db.execute(text(query), params)
        rows = result.fetchall()

        logger.info(f"Distribución clasificación - Filas encontradas: {len(rows)}")
        if rows and len(rows) > 0:
            logger.info(f"Distribución clasificación - Datos: {rows}")

        # Mapeo de colores por clasificación
        color_map = {
            "CONFIRMADOS": "rgba(76, 175, 80, 0.7)",  # Verde
            "PROBABLES": "rgba(255, 193, 7, 0.7)",  # Amarillo
            "SOSPECHOSOS": "rgba(255, 152, 0, 0.7)",  # Naranja
            "EN_ESTUDIO": "rgba(33, 150, 243, 0.7)",  # Azul
            "NEGATIVOS": "rgba(158, 158, 158, 0.7)",  # Gris
            "DESCARTADOS": "rgba(189, 189, 189, 0.7)",  # Gris claro
            "NOTIFICADOS": "rgba(3, 169, 244, 0.7)",  # Celeste
            "CON_RESULTADO_MORTAL": "rgba(244, 67, 54, 0.7)",  # Rojo oscuro
            "SIN_RESULTADO_MORTAL": "rgba(139, 195, 74, 0.7)",  # Verde claro
            "REQUIERE_REVISION": "rgba(156, 39, 176, 0.7)",  # Púrpura
            "SIN_CLASIFICAR": "rgba(224, 224, 224, 0.7)",  # Gris muy claro
        }

        # Preparar datos con colores apropiados
        labels = []
        data_values = []
        colors = []

        for row in rows:
            clasificacion = row[0]
            casos = row[1]

            # Formatear label para mostrar
            label_formateado = clasificacion.replace("_", " ").title()
            labels.append(label_formateado)
            data_values.append(casos)
            colors.append(color_map.get(clasificacion, "rgba(158, 158, 158, 0.7)"))

        # Formato nuevo: BaseChartData compatible
        return {
            "data": {
                "labels": labels,
                "datasets": [
                    {
                        "label": "Casos",
                        "data": [int(v) for v in data_values],
                        "backgroundColor": colors,
                    }
                ],
            }
        }

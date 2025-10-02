"""
Procesadores Python para charts dinámicos
Consulta datos reales de eventos desde la base de datos
"""
import logging
from datetime import date, datetime
from typing import Any, Dict, Optional

import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.procesamiento_archivos.utils.epidemiological_calculations import (
    obtener_fechas_semana_epidemiologica,
    generar_metadata_semanas
)

logger = logging.getLogger(__name__)


class ChartDataProcessor:
    """Procesador de datos para charts del dashboard"""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Convierte string de fecha a objeto date"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    def _apply_common_filters(self, query: str, filtros: Dict[str, Any], params: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
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
                AND id_tipo_eno IN (
                    SELECT id FROM tipo_eno WHERE id_grupo_eno = :grupo_id
                )
            """
            params["grupo_id"] = filtros["grupo_id"]

        if filtros.get("evento_id"):
            query += " AND id_tipo_eno = :evento_id"
            params["evento_id"] = filtros["evento_id"]

        # Filtro por clasificación estrategia
        if filtros.get("clasificaciones"):
            clasificaciones = filtros["clasificaciones"]
            if isinstance(clasificaciones, str):
                clasificaciones = [clasificaciones]
            query += " AND clasificacion_estrategia = ANY(:clasificaciones)"
            params["clasificaciones"] = clasificaciones


        if filtros.get("fecha_desde"):
            query += " AND fecha_minima_evento >= :fecha_desde"
            params["fecha_desde"] = self._parse_date(filtros["fecha_desde"])

        if filtros.get("fecha_hasta"):
            query += " AND fecha_minima_evento <= :fecha_hasta"
            params["fecha_hasta"] = self._parse_date(filtros["fecha_hasta"])

        return query, params

    def _add_classification_filter(self, query: str, filtros: Dict[str, Any], params: Dict[str, Any], table_alias: str = "") -> str:
        """Helper para agregar filtro de clasificación a cualquier query"""
        if filtros.get("clasificaciones"):
            clasificaciones = filtros["clasificaciones"]
            if isinstance(clasificaciones, str):
                clasificaciones = [clasificaciones]

            # Agregar alias de tabla si se proporciona
            field = f"{table_alias}.clasificacion_estrategia" if table_alias else "clasificacion_estrategia"
            query += f" AND {field} = ANY(:clasificaciones)"
            params["clasificaciones"] = clasificaciones

        return query

    def _generate_week_metadata_from_rows(self, rows: list) -> list:
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
            año = int(row[1]) if len(row) > 1 and row[1] is not None else datetime.now().year

            try:
                start_date, end_date = obtener_fechas_semana_epidemiologica(año, semana)
                metadata.append({
                    "year": año,
                    "week": semana,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d")
                })
            except Exception as e:
                logger.warning(f"Error generando metadata para semana {semana}/{año}: {e}")
                continue

        return metadata

    async def process_chart(
        self, 
        chart_config: Any,
        filtros: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Procesa un chart según su función de procesamiento
        
        Args:
            chart_config: Configuración del chart desde DB
            filtros: Filtros aplicados desde el dashboard
            
        Returns:
            Dict con los datos procesados para el chart
        """
        # Mapear función de procesamiento
        processor_map = {
            "curva_epidemiologica": self.process_curva_epidemiologica,
            "corredor_endemico": self.process_corredor_endemico,
            "piramide_poblacional": self.process_piramide_poblacional,
            "mapa_geografico": self.process_mapa_geografico,
            "estacionalidad": self.process_estacionalidad,
            "casos_edad": self.process_casos_edad,
            "intento_suicidio": self.process_intento_suicidio,
            "rabia_animal": self.process_rabia_animal,
            "proporcion_ira": self.process_proporcion_ira,
            "distribucion_clasificacion": self.process_distribucion_clasificacion,
        }
        
        processor_func = processor_map.get(chart_config.funcion_procesamiento)
        if not processor_func:
            logger.error(f"Función de procesamiento no encontrada: {chart_config.funcion_procesamiento}")
            return {
                "error": f"Función de procesamiento no encontrada: {chart_config.funcion_procesamiento}"
            }
        
        # Ejecutar procesador
        try:
            logger.debug(f"Ejecutando procesador {chart_config.funcion_procesamiento} con filtros: {filtros}")
            result = await processor_func(filtros)
            logger.debug(f"Procesador {chart_config.funcion_procesamiento} completado")
            return result
        except Exception as e:
            logger.error(f"Error en procesador {chart_config.funcion_procesamiento}: {str(e)}")
            # Retornar estructura vacía en caso de error
            return {
                "type": chart_config.tipo_visualizacion,
                "data": {
                    "labels": [],
                    "datasets": []
                },
                "error": str(e)
            }
    
    async def process_curva_epidemiologica(self, filtros: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa datos para curva epidemiológica
        Basado en el sistema Chubut: casos por semana epidemiológica
        """
        # Construir query para obtener casos por semana epidemiológica
        # IMPORTANTE: Incluir año epidemiológico para metadata correcta
        query = """
        SELECT
            e.semana_epidemiologica_apertura as semana,
            e.anio_epidemiologico_apertura as año,
            COUNT(*) as casos
        FROM evento e
        LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
        LEFT JOIN localidad l ON est.id_localidad_establecimiento = l.id_localidad_indec
        LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
        WHERE e.semana_epidemiologica_apertura IS NOT NULL
            AND e.anio_epidemiologico_apertura IS NOT NULL
            AND d.id_provincia_indec = 26
        """

        params = {}

        # Aplicar filtros
        if filtros.get("grupo_id"):
            query += """
                AND id_tipo_eno IN (
                    SELECT id FROM tipo_eno WHERE id_grupo_eno = :grupo_id
                )
            """
            params["grupo_id"] = filtros["grupo_id"]

        if filtros.get("evento_id"):
            query += " AND id_tipo_eno = :evento_id"
            params["evento_id"] = filtros["evento_id"]

        # Filtro por clasificación estrategia
        query = self._add_classification_filter(query, filtros, params)

        if filtros.get("fecha_desde"):
            query += " AND fecha_minima_evento >= :fecha_desde"
            params["fecha_desde"] = self._parse_date(filtros["fecha_desde"])

        if filtros.get("fecha_hasta"):
            query += " AND fecha_minima_evento <= :fecha_hasta"
            params["fecha_hasta"] = self._parse_date(filtros["fecha_hasta"])

        query += " GROUP BY semana, año ORDER BY año, semana"

        # Ejecutar query
        result = await self.db.execute(text(query), params)
        rows = result.fetchall()

        logger.info(f"Curva epidemiológica - Filas encontradas: {len(rows)}")
        if rows and len(rows) > 0:
            logger.info(f"Curva epidemiológica - Primeras 3 filas: {rows[:3]}")

        # Si no hay datos, retornar estructura vacía
        if not rows:
            return {
                "type": "line",
                "data": {
                    "labels": [],
                    "datasets": [{
                        "label": "Casos",
                        "data": [],
                        "borderColor": "rgb(75, 192, 192)",
                        "tension": 0.1
                    }],
                    "metadata": []
                }
            }

        # Generar metadata con fechas de inicio/fin
        metadata = self._generate_week_metadata_from_rows(rows)

        # Formatear para el frontend con labels mejorados
        return {
            "type": "line",
            "data": {
                "labels": [f"SE {int(row[0])}/{int(row[1])}" for row in rows],
                "datasets": [{
                    "label": "Casos",
                    "data": [row[2] for row in rows],  # row[2] ahora es casos (antes era row[1])
                    "borderColor": "rgb(75, 192, 192)",
                    "tension": 0.1
                }],
                "metadata": metadata
            }
        }
    
    async def process_corredor_endemico(self, filtros: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa datos para corredor endémico
        Calcula percentiles basados en datos históricos (últimos 5 años)
        Muestra solo las semanas del rango de fechas seleccionado
        """
        from app.features.procesamiento_archivos.utils.epidemiological_calculations import (
            calcular_semana_epidemiologica
        )

        # Determinar rango de semanas a mostrar basado en filtros de fecha
        fecha_desde = self._parse_date(filtros.get("fecha_desde")) if filtros.get("fecha_desde") else None
        fecha_hasta = self._parse_date(filtros.get("fecha_hasta")) if filtros.get("fecha_hasta") else None

        if not fecha_desde or not fecha_hasta:
            return {
                "type": "area",
                "data": {
                    "labels": [],
                    "datasets": [],
                    "metadata": []
                },
                "error": "Se requiere un rango de fechas para el corredor endémico"
            }

        # Calcular semanas epidemiológicas del rango
        semana_inicio, año_inicio = calcular_semana_epidemiologica(fecha_desde)
        semana_fin, año_fin = calcular_semana_epidemiologica(fecha_hasta)

        logger.info(f"Corredor endémico - Rango: SE {semana_inicio}/{año_inicio} - SE {semana_fin}/{año_fin}")

        # Query para obtener datos históricos (últimos 5 años antes del rango)
        query = """
        SELECT
            semana_epidemiologica_apertura as semana,
            anio_epidemiologico_apertura as año,
            COUNT(*) as casos
        FROM evento
        WHERE fecha_minima_evento >= :fecha_historica_inicio
            AND fecha_minima_evento < :fecha_desde
            AND semana_epidemiologica_apertura IS NOT NULL
            AND anio_epidemiologico_apertura IS NOT NULL
        """

        params = {
            "fecha_desde": fecha_desde,
            "fecha_historica_inicio": date(fecha_desde.year - 5, 1, 1)  # 5 años atrás
        }

        logger.info(f"Corredor endémico - DEBUG: fecha_desde={fecha_desde}, fecha_historica_inicio={params['fecha_historica_inicio']}")

        if filtros.get("grupo_id"):
            query += """
                AND id_tipo_eno IN (
                    SELECT id FROM tipo_eno WHERE id_grupo_eno = :grupo_id
                )
            """
            params["grupo_id"] = filtros["grupo_id"]

        if filtros.get("evento_id"):
            query += " AND id_tipo_eno = :evento_id"
            params["evento_id"] = filtros["evento_id"]

        # Filtro por clasificación estrategia
        query = self._add_classification_filter(query, filtros, params)

        query += " GROUP BY semana, año ORDER BY semana, año"

        result = await self.db.execute(text(query), params)
        rows = result.fetchall()

        logger.info(f"Corredor endémico - DEBUG: Registros históricos encontrados: {len(rows)}")
        if rows:
            logger.info(f"Corredor endémico - DEBUG: Primeros 5 registros: {rows[:5]}")

        # Validar que hay suficientes datos históricos
        if not rows or len(rows) < 10:  # Mínimo 10 registros históricos
            return {
                "type": "area",
                "data": {
                    "labels": [],
                    "datasets": [],
                    "metadata": []
                },
                "error": "Datos históricos insuficientes. Se requieren al menos 3 años de datos históricos para calcular el corredor endémico."
            }
        
        # Procesar datos para calcular percentiles
        df = pd.DataFrame(rows, columns=['semana', 'año', 'casos'])

        logger.info(f"Corredor endémico - DEBUG: DataFrame shape: {df.shape}")
        logger.info(f"Corredor endémico - DEBUG: DataFrame head:\n{df.head(10)}")

        # Validar que tenemos al menos 3 años diferentes de datos
        años_unicos = df['año'].nunique()
        años_lista = sorted(df['año'].unique().tolist())
        logger.info(f"Corredor endémico - Años únicos en histórico: {años_unicos}")
        logger.info(f"Corredor endémico - DEBUG: Lista de años: {años_lista}")

        if años_unicos < 3:
            año_texto = "año" if años_unicos == 1 else "años"
            return {
                "type": "area",
                "data": {
                    "labels": [],
                    "datasets": [],
                    "metadata": []
                },
                "error": f"Datos históricos insuficientes. Se encontró {años_unicos} {año_texto}, se requieren al menos 3 años de datos históricos."
            }

        # Generar lista de semanas del rango seleccionado
        weeks_in_range = []
        if año_inicio == año_fin:
            # Mismo año
            weeks_in_range = list(range(semana_inicio, semana_fin + 1))
        else:
            # Múltiples años - para simplificar, mostrar todas las semanas
            # TODO: Manejar rangos multi-año correctamente
            weeks_in_range = list(range(1, 53))

        logger.info(f"Corredor endémico - Semanas a mostrar: {len(weeks_in_range)} semanas")

        # Calcular percentiles solo para las semanas en el rango
        percentiles = df.groupby('semana')['casos'].agg([
            ('minimo', lambda x: x.quantile(0.25)),
            ('mediana', lambda x: x.quantile(0.5)),
            ('maximo', lambda x: x.quantile(0.75))
        ]).reset_index()

        # Filtrar percentiles para solo las semanas del rango
        weeks_df = pd.DataFrame({'semana': weeks_in_range})
        percentiles = weeks_df.merge(percentiles, on='semana', how='left').fillna(0)
        
        # Obtener casos actuales para el período seleccionado
        current_query = """
        SELECT
            semana_epidemiologica_apertura as semana,
            COUNT(*) as casos
        FROM evento
        WHERE fecha_minima_evento >= :fecha_desde
            AND fecha_minima_evento <= :fecha_hasta
            AND semana_epidemiologica_apertura IS NOT NULL
        """

        current_params = {
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta
        }

        if filtros.get("grupo_id"):
            current_query += """
                AND id_tipo_eno IN (
                    SELECT id FROM tipo_eno WHERE id_grupo_eno = :grupo_id
                )
            """
            current_params["grupo_id"] = filtros["grupo_id"]

        if filtros.get("evento_id"):
            current_query += " AND id_tipo_eno = :evento_id"
            current_params["evento_id"] = filtros["evento_id"]

        # Filtro por clasificación estrategia
        current_query = self._add_classification_filter(current_query, filtros, current_params)

        current_query += " GROUP BY semana ORDER BY semana"

        current_result = await self.db.execute(text(current_query), current_params)
        current_rows = current_result.fetchall()

        current_df = pd.DataFrame(current_rows, columns=['semana', 'casos']) if current_rows else pd.DataFrame()

        # Merge casos actuales con las semanas del rango
        if not current_df.empty:
            current_data = weeks_df.merge(current_df, on='semana', how='left').fillna(0)
            casos_actuales = current_data['casos'].tolist()
        else:
            casos_actuales = [0] * len(weeks_in_range)

        # Generar metadata para las semanas del rango
        metadata = []
        for week in weeks_in_range:
            try:
                # Usar año correspondiente (año_inicio para simplificar, o año_fin si es multi-año)
                year_for_week = año_inicio if año_inicio == año_fin else año_fin
                start_date, end_date = obtener_fechas_semana_epidemiologica(year_for_week, week)
                metadata.append({
                    "year": year_for_week,
                    "week": week,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d")
                })
            except Exception as e:
                logger.warning(f"Error generando metadata para semana {week}/{year_for_week}: {e}")
                continue

        # Generar labels
        year_label = año_inicio if año_inicio == año_fin else f"{año_inicio}-{año_fin}"
        labels = [f"SE {int(week)}/{year_label}" for week in weeks_in_range]

        return {
            "type": "area",
            "data": {
                "labels": labels,
                "datasets": [
                    {
                        "label": "Máximo (P75)",
                        "data": percentiles['maximo'].tolist(),
                        "borderColor": "red",
                        "backgroundColor": "rgba(255, 0, 0, 0.1)",
                        "fill": "+1"
                    },
                    {
                        "label": "Mediana (P50)",
                        "data": percentiles['mediana'].tolist(),
                        "borderColor": "orange",
                        "backgroundColor": "rgba(255, 165, 0, 0.1)",
                        "fill": False
                    },
                    {
                        "label": "Mínimo (P25)",
                        "data": percentiles['minimo'].tolist(),
                        "borderColor": "green",
                        "backgroundColor": "rgba(0, 255, 0, 0.1)",
                        "fill": False
                    },
                    {
                        "label": "Casos actuales",
                        "data": casos_actuales,
                        "borderColor": "blue",
                        "type": "line",
                        "fill": False
                    }
                ],
                "metadata": metadata
            }
        }
    
    async def process_piramide_poblacional(self, filtros: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa datos para pirámide poblacional - Solo Chubut
        """
        # Query para obtener distribución por edad y sexo
        query = """
        SELECT
            CASE
                WHEN e.edad_anos_al_momento_apertura < 5 THEN '0-4'
                WHEN e.edad_anos_al_momento_apertura < 10 THEN '5-9'
                WHEN e.edad_anos_al_momento_apertura < 15 THEN '10-14'
                WHEN e.edad_anos_al_momento_apertura < 20 THEN '15-19'
                WHEN e.edad_anos_al_momento_apertura < 25 THEN '20-24'
                WHEN e.edad_anos_al_momento_apertura < 30 THEN '25-29'
                WHEN e.edad_anos_al_momento_apertura < 35 THEN '30-34'
                WHEN e.edad_anos_al_momento_apertura < 40 THEN '35-39'
                WHEN e.edad_anos_al_momento_apertura < 45 THEN '40-44'
                WHEN e.edad_anos_al_momento_apertura < 50 THEN '45-49'
                WHEN e.edad_anos_al_momento_apertura < 55 THEN '50-54'
                WHEN e.edad_anos_al_momento_apertura < 60 THEN '55-59'
                WHEN e.edad_anos_al_momento_apertura < 65 THEN '60-64'
                ELSE '65+'
            END as grupo_edad,
            COALESCE(c.sexo_biologico, 'NO_ESPECIFICADO') as sexo,
            COUNT(*) as casos
        FROM evento e
        LEFT JOIN ciudadano c ON e.codigo_ciudadano = c.codigo_ciudadano
        LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
        LEFT JOIN localidad l ON est.id_localidad_establecimiento = l.id_localidad_indec
        LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
        WHERE e.edad_anos_al_momento_apertura IS NOT NULL
            AND d.id_provincia_indec = 26
        """
        
        params = {}
        
        if filtros.get("grupo_id"):
            query += """
                AND e.id_tipo_eno IN (
                    SELECT id FROM tipo_eno WHERE id_grupo_eno = :grupo_id
                )
            """
            params["grupo_id"] = filtros["grupo_id"]
            
        if filtros.get("evento_id"):
            query += " AND e.id_tipo_eno = :evento_id"
            params["evento_id"] = filtros["evento_id"]

        # Filtro por clasificación estrategia
        query = self._add_classification_filter(query, filtros, params, "e")

        # CRÍTICO: Agregar filtros de fecha
        if filtros.get("fecha_desde"):
            query += " AND e.fecha_minima_evento >= :fecha_desde"
            params["fecha_desde"] = self._parse_date(filtros["fecha_desde"])

        if filtros.get("fecha_hasta"):
            query += " AND e.fecha_minima_evento <= :fecha_hasta"
            params["fecha_hasta"] = self._parse_date(filtros["fecha_hasta"])

        query += " GROUP BY grupo_edad, sexo ORDER BY grupo_edad"
        
        result = await self.db.execute(text(query), params)
        rows = result.fetchall()
        
        logger.info(f"Pirámide poblacional - Filas encontradas: {len(rows)}")
        if rows and len(rows) > 0:
            logger.info(f"Pirámide poblacional - Primeras 5 filas: {rows[:5]}")
            logger.info(f"Pirámide poblacional - Valores de sexo encontrados: {set([row[1] for row in rows])}")
        
        # Procesar para formato de pirámide
        age_groups = ["0-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", 
                     "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65+"]
        
        male_data = {g: 0 for g in age_groups}
        female_data = {g: 0 for g in age_groups}
        
        for row in rows:
            grupo_edad, sexo, casos = row
            if sexo in ['MASCULINO', 'M']:
                male_data[grupo_edad] = -casos  # Negativos para el lado izquierdo
            elif sexo in ['FEMENINO', 'F']:
                female_data[grupo_edad] = casos
        
        # Preparar datos para D3.js - formato de pirámide poblacional
        # Incluir todos los grupos de edad, incluso con 0 casos
        pyramid_data = []
        for age_group in age_groups:
            male_count = abs(male_data[age_group])  # Convertir negativos a positivos
            female_count = female_data[age_group]
            
            # Siempre agregar entrada para masculino
            pyramid_data.append({
                "age": age_group,
                "sex": "M",
                "value": male_count
            })
            
            # Siempre agregar entrada para femenino
            pyramid_data.append({
                "age": age_group,
                "sex": "F", 
                "value": female_count
            })
        
        return {
            "type": "d3_pyramid",
            "data": pyramid_data,
            "metadata": {
                "age_groups": age_groups,
                "total_male": sum(abs(male_data[g]) for g in age_groups),
                "total_female": sum(female_data[g] for g in age_groups)
            }
        }

    async def process_mapa_geografico(self, filtros: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa datos para mapa geográfico con departamentos de Chubut
        """
        from datetime import datetime
        from app.core.constants.geografia_chubut import (
            DEPARTAMENTOS_CHUBUT,
            POBLACION_DEPARTAMENTOS,
            get_zona_ugd
        )

        # Query para obtener casos por departamento
        query = """
        SELECT
            COALESCE(d.id_departamento_indec, 0) as codigo_indec,
            COUNT(*) as casos
        FROM evento e
        LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
        LEFT JOIN localidad l ON est.id_localidad_establecimiento = l.id_localidad_indec
        LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
        WHERE d.id_provincia_indec = 26
        """

        params = {"provincia_id": 26}

        if filtros.get("grupo_id"):
            query += """
                AND e.id_tipo_eno IN (
                    SELECT id FROM tipo_eno WHERE id_grupo_eno = :grupo_id
                )
            """
            params["grupo_id"] = filtros["grupo_id"]

        if filtros.get("evento_id"):
            query += " AND e.id_tipo_eno = :evento_id"
            params["evento_id"] = filtros["evento_id"]

        # Filtro por clasificación estrategia
        query = self._add_classification_filter(query, filtros, params, "e")

        if filtros.get("fecha_desde"):
            query += " AND e.fecha_minima_evento >= :fecha_desde"
            # Convert string to date if necessary
            fecha_desde = filtros["fecha_desde"]
            if isinstance(fecha_desde, str):
                fecha_desde = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
            params["fecha_desde"] = fecha_desde

        if filtros.get("fecha_hasta"):
            query += " AND e.fecha_minima_evento <= :fecha_hasta"
            # Convert string to date if necessary
            fecha_hasta = filtros["fecha_hasta"]
            if isinstance(fecha_hasta, str):
                fecha_hasta = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
            params["fecha_hasta"] = fecha_hasta

        query += " GROUP BY d.id_departamento_indec"

        result = await self.db.execute(text(query), params)
        rows = result.fetchall()

        # Crear mapa de casos por departamento
        casos_por_departamento = {row.codigo_indec: row.casos for row in rows if row.codigo_indec}

        # Construir datos para todos los departamentos
        departamentos_data = []
        for codigo_indec in DEPARTAMENTOS_CHUBUT.keys():
            casos = casos_por_departamento.get(codigo_indec, 0)
            poblacion = POBLACION_DEPARTAMENTOS.get(codigo_indec, 0)
            tasa_incidencia = round((casos / poblacion) * 100000, 2) if poblacion > 0 else 0.0

            departamentos_data.append({
                "codigo_indec": codigo_indec,
                "nombre": DEPARTAMENTOS_CHUBUT[codigo_indec],
                "zona_ugd": get_zona_ugd(codigo_indec),
                "poblacion": poblacion,
                "casos": casos,
                "tasa_incidencia": tasa_incidencia
            })

        logger.info(f"Mapa geográfico - Departamentos con casos: {len(casos_por_departamento)}")

        return {
            "type": "mapa",
            "data": {
                "departamentos": departamentos_data,
                "total_casos": sum(casos_por_departamento.values())
            }
        }

    async def process_estacionalidad(self, filtros: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa datos para estacionalidad mensual - Solo Chubut
        Muestra la distribución de casos por mes del año
        """
        query = """
        SELECT
            EXTRACT(MONTH FROM e.fecha_minima_evento) as mes,
            COUNT(*) as casos
        FROM evento e
        LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
        LEFT JOIN localidad l ON est.id_localidad_establecimiento = l.id_localidad_indec
        LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
        WHERE e.fecha_minima_evento IS NOT NULL
            AND d.id_provincia_indec = 26
        """

        params = {}

        if filtros.get("grupo_id"):
            query += """
                AND e.id_tipo_eno IN (
                    SELECT id FROM tipo_eno WHERE id_grupo_eno = :grupo_id
                )
            """
            params["grupo_id"] = filtros["grupo_id"]

        if filtros.get("evento_id"):
            query += " AND e.id_tipo_eno = :evento_id"
            params["evento_id"] = filtros["evento_id"]

        # Filtro por clasificación estrategia
        query = self._add_classification_filter(query, filtros, params, "e")

        # Filtros de fecha
        if filtros.get("fecha_desde"):
            query += " AND e.fecha_minima_evento >= :fecha_desde"
            params["fecha_desde"] = self._parse_date(filtros["fecha_desde"])

        if filtros.get("fecha_hasta"):
            query += " AND e.fecha_minima_evento <= :fecha_hasta"
            params["fecha_hasta"] = self._parse_date(filtros["fecha_hasta"])

        query += " GROUP BY mes ORDER BY mes"

        result = await self.db.execute(text(query), params)
        rows = result.fetchall()

        logger.info(f"Estacionalidad - Filas encontradas: {len(rows)}")

        # Nombres de meses en español
        meses_nombres = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]

        # Crear diccionario con todos los meses (inicializar en 0)
        casos_por_mes = {i: 0 for i in range(1, 13)}

        # Llenar con los datos obtenidos
        for row in rows:
            mes = int(row[0]) if row[0] else 0
            if 1 <= mes <= 12:
                casos_por_mes[mes] = row[1]

        if not rows:
            return {
                "type": "bar",
                "data": {
                    "labels": meses_nombres,
                    "datasets": [{
                        "label": "Casos por mes",
                        "data": [0] * 12,
                        "backgroundColor": "rgba(54, 162, 235, 0.5)"
                    }]
                }
            }

        return {
            "type": "bar",
            "data": {
                "labels": meses_nombres,
                "datasets": [{
                    "label": "Casos por mes",
                    "data": [casos_por_mes[i] for i in range(1, 13)],
                    "backgroundColor": "rgba(54, 162, 235, 0.5)"
                }]
            }
        }

    async def process_casos_edad(self, filtros: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa datos para casos por grupos de edad - Solo Chubut
        """
        query = """
        SELECT
            CASE
                WHEN e.edad_anos_al_momento_apertura < 1 THEN '< 1 año'
                WHEN e.edad_anos_al_momento_apertura < 5 THEN '1-4'
                WHEN e.edad_anos_al_momento_apertura < 10 THEN '5-9'
                WHEN e.edad_anos_al_momento_apertura < 15 THEN '10-14'
                WHEN e.edad_anos_al_momento_apertura < 20 THEN '15-19'
                WHEN e.edad_anos_al_momento_apertura < 30 THEN '20-29'
                WHEN e.edad_anos_al_momento_apertura < 40 THEN '30-39'
                WHEN e.edad_anos_al_momento_apertura < 50 THEN '40-49'
                WHEN e.edad_anos_al_momento_apertura < 60 THEN '50-59'
                WHEN e.edad_anos_al_momento_apertura < 70 THEN '60-69'
                ELSE '70+'
            END as grupo_edad,
            COUNT(*) as casos
        FROM evento e
        LEFT JOIN ciudadano c ON e.codigo_ciudadano = c.codigo_ciudadano
        LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
        LEFT JOIN localidad l ON est.id_localidad_establecimiento = l.id_localidad_indec
        LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
        WHERE d.id_provincia_indec = 26
        """

        params = {}

        if filtros.get("grupo_id"):
            query += """
                AND e.id_tipo_eno IN (
                    SELECT id FROM tipo_eno WHERE id_grupo_eno = :grupo_id
                )
            """
            params["grupo_id"] = filtros["grupo_id"]

        if filtros.get("evento_id"):
            query += " AND e.id_tipo_eno = :evento_id"
            params["evento_id"] = filtros["evento_id"]

        # Filtro por clasificación estrategia
        query = self._add_classification_filter(query, filtros, params, "e")

        # CRÍTICO: Agregar filtros de fecha
        if filtros.get("fecha_desde"):
            query += " AND e.fecha_minima_evento >= :fecha_desde"
            params["fecha_desde"] = self._parse_date(filtros["fecha_desde"])

        if filtros.get("fecha_hasta"):
            query += " AND e.fecha_minima_evento <= :fecha_hasta"
            params["fecha_hasta"] = self._parse_date(filtros["fecha_hasta"])

        query += " GROUP BY grupo_edad ORDER BY MIN(e.edad_anos_al_momento_apertura)"
        
        result = await self.db.execute(text(query), params)
        rows = result.fetchall()
        
        logger.info(f"Casos por edad - Filas encontradas: {len(rows)}")
        if rows and len(rows) > 0:
            logger.info(f"Casos por edad - Grupos: {rows}")
        
        if not rows:
            return {
                "type": "bar",
                "data": {
                    "labels": [],
                    "datasets": [{
                        "label": "Casos por edad",
                        "data": [],
                        "backgroundColor": "rgba(153, 102, 255, 0.5)"
                    }]
                }
            }
        
        return {
            "type": "bar",
            "data": {
                "labels": [row[0] for row in rows],
                "datasets": [{
                    "label": "Casos por edad",
                    "data": [row[1] for row in rows],
                    "backgroundColor": "rgba(153, 102, 255, 0.5)"
                }]
            }
        }
    
    async def process_intento_suicidio(self, filtros: Dict[str, Any]) -> Dict[str, Any]:
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
        FROM evento e
        WHERE e.id_tipo_eno IN (
            SELECT id FROM tipo_eno WHERE LOWER(nombre) LIKE '%suicid%'
        )
        """
        
        params = {}

        if filtros.get("evento_id"):
            query += " AND e.id_tipo_eno = :evento_id"
            params["evento_id"] = filtros["evento_id"]

        # CRÍTICO: Agregar filtros de fecha
        if filtros.get("fecha_desde"):
            query += " AND e.fecha_minima_evento >= :fecha_desde"
            params["fecha_desde"] = self._parse_date(filtros["fecha_desde"])

        if filtros.get("fecha_hasta"):
            query += " AND e.fecha_minima_evento <= :fecha_hasta"
            params["fecha_hasta"] = self._parse_date(filtros["fecha_hasta"])

        query += " GROUP BY categoria"
        
        result = await self.db.execute(text(query), params)
        rows = result.fetchall()
        
        if not rows:
            return {
                "type": "bar",
                "data": {
                    "labels": [],
                    "datasets": [{
                        "label": "Casos",
                        "data": [],
                        "backgroundColor": []
                    }]
                }
            }
        
        # TODO: Implementar categorización específica cuando tengamos campos de método
        return {
            "type": "bar",
            "data": {
                "labels": ["Total registrado"],
                "datasets": [{
                    "label": "Casos",
                    "data": [rows[0][1] if rows else 0],
                    "backgroundColor": ["rgba(255, 99, 132, 0.5)"]
                }]
            }
        }
    
    async def process_rabia_animal(self, filtros: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa datos específicos para rabia animal
        """
        # Similar al anterior, específico para zoonosis
        query = """
        SELECT 
            COALESCE(a.especie, 'No especificado') as especie,
            COUNT(*) as casos
        FROM evento e
        LEFT JOIN animal a ON e.id_animal = a.id
        WHERE e.id_tipo_eno IN (
            SELECT id FROM tipo_eno WHERE LOWER(nombre) LIKE '%rabia%'
        )
        """
        
        params = {}

        if filtros.get("evento_id"):
            query += " AND e.id_tipo_eno = :evento_id"
            params["evento_id"] = filtros["evento_id"]

        # CRÍTICO: Agregar filtros de fecha
        if filtros.get("fecha_desde"):
            query += " AND e.fecha_minima_evento >= :fecha_desde"
            params["fecha_desde"] = self._parse_date(filtros["fecha_desde"])

        if filtros.get("fecha_hasta"):
            query += " AND e.fecha_minima_evento <= :fecha_hasta"
            params["fecha_hasta"] = self._parse_date(filtros["fecha_hasta"])

        query += " GROUP BY especie"
        
        result = await self.db.execute(text(query), params)
        rows = result.fetchall()
        
        if not rows:
            return {
                "type": "bar",
                "data": {
                    "labels": [],
                    "datasets": [{
                        "label": "Casos por especie",
                        "data": [],
                        "backgroundColor": []
                    }]
                }
            }
        
        return {
            "type": "bar",
            "data": {
                "labels": [row[0] for row in rows],
                "datasets": [{
                    "label": "Casos por especie",
                    "data": [row[1] for row in rows],
                    "backgroundColor": [
                        "rgba(255, 159, 64, 0.5)",
                        "rgba(153, 102, 255, 0.5)",
                        "rgba(75, 192, 192, 0.5)",
                        "rgba(255, 99, 132, 0.5)"
                    ][:len(rows)]
                }]
            }
        }
    
    async def process_proporcion_ira(self, filtros: Dict[str, Any]) -> Dict[str, Any]:
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
        FROM evento e
        JOIN tipo_eno t ON e.id_tipo_eno = t.id
        JOIN grupo_eno g ON t.id_grupo_eno = g.id
        WHERE LOWER(g.nombre) LIKE '%respiratoria%' 
           OR LOWER(t.nombre) LIKE '%ira%' 
           OR LOWER(t.nombre) LIKE '%respiratoria%'
        """
        
        params = {}
        
        if filtros.get("grupo_id"):
            query += " AND t.id_grupo_eno = :grupo_id"
            params["grupo_id"] = filtros["grupo_id"]
            
        if filtros.get("evento_id"):
            query += " AND e.id_tipo_eno = :evento_id"
            params["evento_id"] = filtros["evento_id"]
            
        if filtros.get("fecha_desde"):
            query += " AND e.fecha_minima_evento >= :fecha_desde"
            params["fecha_desde"] = self._parse_date(filtros["fecha_desde"])
            
        if filtros.get("fecha_hasta"):
            query += " AND e.fecha_minima_evento <= :fecha_hasta"
            params["fecha_hasta"] = self._parse_date(filtros["fecha_hasta"])
            
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
                    "datasets": [{
                        "data": [1],
                        "backgroundColor": ["rgba(200, 200, 200, 0.5)"]
                    }]
                }
            }
        
        # Calcular total para proporciones
        total_casos = sum(row[1] for row in rows)
        
        return {
            "type": "pie",
            "data": {
                "labels": [row[0] for row in rows],
                "datasets": [{
                    "data": [row[1] for row in rows],
                    "backgroundColor": [
                        "rgba(54, 162, 235, 0.7)",   # IRA - Azul
                        "rgba(255, 99, 132, 0.7)",   # IRAG - Rojo
                        "rgba(255, 206, 86, 0.7)",   # Neumonía - Amarillo
                        "rgba(75, 192, 192, 0.7)",   # Bronquiolitis - Verde
                        "rgba(153, 102, 255, 0.7)",  # Otras - Púrpura
                    ][:len(rows)]
                }]
            },
            "metadata": {
                "total_casos": total_casos,
                "proporciones": [
                    {
                        "tipo": row[0],
                        "casos": row[1],
                        "porcentaje": round((row[1] / total_casos) * 100, 2) if total_casos > 0 else 0
                    }
                    for row in rows
                ]
            }
        }

    async def process_distribucion_clasificacion(self, filtros: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa datos para distribución por clasificación estratégica - Solo Chubut
        Muestra casos por tipo de clasificación (CONFIRMADOS, PROBABLES, SOSPECHOSOS, etc.)
        """
        query = """
        SELECT
            COALESCE(e.clasificacion_estrategia, 'SIN_CLASIFICAR') as clasificacion,
            COUNT(*) as casos
        FROM evento e
        LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
        LEFT JOIN localidad l ON est.id_localidad_establecimiento = l.id_localidad_indec
        LEFT JOIN departamento d ON l.id_departamento_indec = d.id_departamento_indec
        WHERE d.id_provincia_indec = 26
        """

        params = {}

        if filtros.get("grupo_id"):
            query += """
                AND e.id_tipo_eno IN (
                    SELECT id FROM tipo_eno WHERE id_grupo_eno = :grupo_id
                )
            """
            params["grupo_id"] = filtros["grupo_id"]

        if filtros.get("evento_id"):
            query += " AND e.id_tipo_eno = :evento_id"
            params["evento_id"] = filtros["evento_id"]

        # Filtro por clasificaciones (usar helper consistente)
        query = self._add_classification_filter(query, filtros, params, table_alias="e")

        # Filtros de fecha
        if filtros.get("fecha_desde"):
            query += " AND e.fecha_minima_evento >= :fecha_desde"
            params["fecha_desde"] = self._parse_date(filtros["fecha_desde"])

        if filtros.get("fecha_hasta"):
            query += " AND e.fecha_minima_evento <= :fecha_hasta"
            params["fecha_hasta"] = self._parse_date(filtros["fecha_hasta"])

        query += " GROUP BY clasificacion ORDER BY casos DESC"

        result = await self.db.execute(text(query), params)
        rows = result.fetchall()

        logger.info(f"Distribución clasificación - Filas encontradas: {len(rows)}")
        if rows and len(rows) > 0:
            logger.info(f"Distribución clasificación - Datos: {rows}")

        if not rows:
            return {
                "type": "pie",
                "data": {
                    "labels": ["Sin datos"],
                    "datasets": [{
                        "data": [1],
                        "backgroundColor": ["rgba(200, 200, 200, 0.5)"]
                    }]
                }
            }

        # Mapeo de colores por clasificación
        color_map = {
            "CONFIRMADOS": "rgba(76, 175, 80, 0.7)",      # Verde
            "PROBABLES": "rgba(255, 193, 7, 0.7)",        # Amarillo
            "SOSPECHOSOS": "rgba(255, 152, 0, 0.7)",      # Naranja
            "EN_ESTUDIO": "rgba(33, 150, 243, 0.7)",      # Azul
            "NEGATIVOS": "rgba(158, 158, 158, 0.7)",      # Gris
            "DESCARTADOS": "rgba(189, 189, 189, 0.7)",    # Gris claro
            "NOTIFICADOS": "rgba(3, 169, 244, 0.7)",      # Celeste
            "CON_RESULTADO_MORTAL": "rgba(244, 67, 54, 0.7)",   # Rojo oscuro
            "SIN_RESULTADO_MORTAL": "rgba(139, 195, 74, 0.7)",  # Verde claro
            "REQUIERE_REVISION": "rgba(156, 39, 176, 0.7)",     # Púrpura
            "SIN_CLASIFICAR": "rgba(224, 224, 224, 0.7)",       # Gris muy claro
        }

        # Preparar datos con colores apropiados
        labels = []
        data = []
        colors = []

        for row in rows:
            clasificacion = row[0]
            casos = row[1]

            # Formatear label para mostrar
            label_formateado = clasificacion.replace("_", " ").title()
            labels.append(label_formateado)
            data.append(casos)
            colors.append(color_map.get(clasificacion, "rgba(158, 158, 158, 0.7)"))

        total_casos = sum(data)

        return {
            "type": "pie",
            "data": {
                "labels": labels,
                "datasets": [{
                    "data": data,
                    "backgroundColor": colors
                }]
            },
            "metadata": {
                "total_casos": total_casos,
                "proporciones": [
                    {
                        "clasificacion": labels[i],
                        "casos": data[i],
                        "porcentaje": round((data[i] / total_casos) * 100, 2) if total_casos > 0 else 0
                    }
                    for i in range(len(labels))
                ]
            }
        }
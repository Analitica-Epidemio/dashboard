"""
Procesadores Python para charts dinámicos
Consulta datos reales de eventos desde la base de datos
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, date
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func, and_, or_
import pandas as pd
from app.domains.eventos.models import Evento, TipoEno, GrupoEno

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
            "distribucion_geografica": self.process_distribucion_geografica,
            "totales_historicos": self.process_totales_historicos,
            "torta_sexo": self.process_torta_sexo,
            "casos_edad": self.process_casos_edad,
            "intento_suicidio": self.process_intento_suicidio,
            "rabia_animal": self.process_rabia_animal,
            "proporcion_ira": self.process_proporcion_ira,
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
        query = """
        SELECT 
            semana_epidemiologica_apertura as semana,
            COUNT(*) as casos
        FROM evento
        WHERE semana_epidemiologica_apertura IS NOT NULL
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
            
        query += " GROUP BY semana ORDER BY semana"
        
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
                    }]
                }
            }
        
        # Formatear para el frontend
        return {
            "type": "line",
            "data": {
                "labels": [f"Semana {int(row[0])}" for row in rows],
                "datasets": [{
                    "label": "Casos",
                    "data": [row[1] for row in rows],
                    "borderColor": "rgb(75, 192, 192)",
                    "tension": 0.1
                }]
            }
        }
    
    async def process_corredor_endemico(self, filtros: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa datos para corredor endémico
        Calcula percentiles basados en datos históricos
        """
        # Query para obtener datos históricos por semana
        query = """
        SELECT 
            semana_epidemiologica_apertura as semana,
            anio_epidemiologico_apertura as año,
            COUNT(*) as casos
        FROM evento
        WHERE fecha_minima_evento >= CURRENT_DATE - INTERVAL '5 years'
            AND semana_epidemiologica_apertura IS NOT NULL
        """
        
        params = {}
        
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
        
        if not rows:
            # Retornar datos vacíos si no hay histórico
            weeks = list(range(1, 53))
            return {
                "type": "area",
                "data": {
                    "labels": [f"S{w}" for w in weeks],
                    "datasets": [
                        {
                            "label": "Máximo",
                            "data": [0] * 52,
                            "borderColor": "red",
                            "backgroundColor": "rgba(255, 0, 0, 0.1)",
                            "fill": "+1"
                        },
                        {
                            "label": "Mediana",
                            "data": [0] * 52,
                            "borderColor": "orange",
                            "backgroundColor": "rgba(255, 165, 0, 0.1)",
                            "fill": False
                        },
                        {
                            "label": "Mínimo",
                            "data": [0] * 52,
                            "borderColor": "green",
                            "backgroundColor": "rgba(0, 255, 0, 0.1)",
                            "fill": False
                        }
                    ]
                }
            }
        
        # Procesar datos para calcular percentiles
        df = pd.DataFrame(rows, columns=['semana', 'año', 'casos'])
        
        # Calcular percentiles por semana
        percentiles = df.groupby('semana')['casos'].agg([
            ('minimo', lambda x: x.quantile(0.25)),
            ('mediana', lambda x: x.quantile(0.5)),
            ('maximo', lambda x: x.quantile(0.75))
        ]).reset_index()
        
        # Asegurar que tenemos todas las semanas
        all_weeks = pd.DataFrame({'semana': range(1, 53)})
        percentiles = all_weeks.merge(percentiles, on='semana', how='left').fillna(0)
        
        # Obtener casos del año actual
        current_year_query = """
        SELECT 
            semana_epidemiologica_apertura as semana,
            COUNT(*) as casos
        FROM evento
        WHERE anio_epidemiologico_apertura = EXTRACT(YEAR FROM CURRENT_DATE)
        """
        
        if filtros.get("grupo_id"):
            current_year_query += """
                AND id_tipo_eno IN (
                    SELECT id FROM tipo_eno WHERE id_grupo_eno = :grupo_id
                )
            """
            
        if filtros.get("evento_id"):
            current_year_query += " AND id_tipo_eno = :evento_id"

        # Filtro por clasificación estrategia
        current_year_query = self._add_classification_filter(current_year_query, filtros, params)

        current_year_query += " GROUP BY semana ORDER BY semana"
        
        current_result = await self.db.execute(text(current_year_query), params)
        current_rows = current_result.fetchall()
        
        current_df = pd.DataFrame(current_rows, columns=['semana', 'casos']) if current_rows else pd.DataFrame()
        
        # Merge con todas las semanas
        if not current_df.empty:
            current_data = all_weeks.merge(current_df, on='semana', how='left').fillna(0)
            casos_actuales = current_data['casos'].tolist()
        else:
            casos_actuales = [0] * 52
        
        return {
            "type": "area",
            "data": {
                "labels": [f"S{int(i)}" for i in range(1, 53)],
                "datasets": [
                    {
                        "label": "Máximo",
                        "data": percentiles['maximo'].tolist(),
                        "borderColor": "red",
                        "backgroundColor": "rgba(255, 0, 0, 0.1)",
                        "fill": "+1"
                    },
                    {
                        "label": "Mediana",
                        "data": percentiles['mediana'].tolist(),
                        "borderColor": "orange",
                        "backgroundColor": "rgba(255, 165, 0, 0.1)",
                        "fill": False
                    },
                    {
                        "label": "Mínimo",
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
                ]
            }
        }
    
    async def process_piramide_poblacional(self, filtros: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa datos para pirámide poblacional
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
        WHERE e.edad_anos_al_momento_apertura IS NOT NULL
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
    
    async def process_distribucion_geografica(self, filtros: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa datos para distribución geográfica (por departamento/establecimiento)
        """
        query = """
        SELECT 
            COALESCE(est.nombre, 'Sin datos') as lugar,
            COUNT(*) as casos
        FROM evento e
        LEFT JOIN establecimiento est ON e.id_establecimiento_notificacion = est.id
        WHERE 1=1
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

        query += " GROUP BY lugar ORDER BY casos DESC LIMIT 10"
        
        result = await self.db.execute(text(query), params)
        rows = result.fetchall()
        
        logger.info(f"Distribución geográfica - Filas encontradas: {len(rows)}")
        if rows and len(rows) > 0:
            logger.info(f"Distribución geográfica - Top 3 lugares: {rows[:3]}")
        
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
        
        return {
            "type": "pie",
            "data": {
                "labels": [row[0] for row in rows],
                "datasets": [{
                    "data": [row[1] for row in rows],
                    "backgroundColor": [
                        "rgba(255, 99, 132, 0.5)",
                        "rgba(54, 162, 235, 0.5)",
                        "rgba(255, 206, 86, 0.5)",
                        "rgba(75, 192, 192, 0.5)",
                        "rgba(153, 102, 255, 0.5)",
                        "rgba(255, 159, 64, 0.5)",
                        "rgba(199, 199, 199, 0.5)",
                        "rgba(83, 102, 255, 0.5)",
                        "rgba(255, 99, 255, 0.5)",
                        "rgba(99, 255, 132, 0.5)"
                    ]
                }]
            }
        }
    
    async def process_totales_historicos(self, filtros: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa datos para totales históricos por año
        """
        query = """
        SELECT 
            anio_epidemiologico_apertura as año,
            COUNT(*) as casos
        FROM evento
        WHERE anio_epidemiologico_apertura IS NOT NULL
        """
        
        params = {}
        
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

        query += " GROUP BY año ORDER BY año"
        
        result = await self.db.execute(text(query), params)
        rows = result.fetchall()
        
        if not rows:
            return {
                "type": "bar",
                "data": {
                    "labels": [],
                    "datasets": [{
                        "label": "Casos totales",
                        "data": [],
                        "backgroundColor": "rgba(75, 192, 192, 0.5)"
                    }]
                }
            }
        
        return {
            "type": "bar",
            "data": {
                "labels": [int(row[0]) for row in rows],
                "datasets": [{
                    "label": "Casos totales",
                    "data": [row[1] for row in rows],
                    "backgroundColor": "rgba(75, 192, 192, 0.5)"
                }]
            }
        }
    
    async def process_torta_sexo(self, filtros: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa datos para distribución por sexo
        """
        query = """
        SELECT 
            CASE 
                WHEN c.sexo_biologico = 'MASCULINO' THEN 'Masculino'
                WHEN c.sexo_biologico = 'FEMENINO' THEN 'Femenino'
                WHEN c.sexo_biologico = 'NO_ESPECIFICADO' THEN 'No especificado'
                ELSE 'Sin datos'
            END as sexo,
            COUNT(*) as casos
        FROM evento e
        LEFT JOIN ciudadano c ON e.codigo_ciudadano = c.codigo_ciudadano
        WHERE 1=1
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

        query += " GROUP BY sexo"
        
        result = await self.db.execute(text(query), params)
        rows = result.fetchall()
        
        logger.info(f"Torta sexo - Filas encontradas: {len(rows)}")
        if rows and len(rows) > 0:
            logger.info(f"Torta sexo - Datos: {rows}")
        
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
        
        return {
            "type": "pie",
            "data": {
                "labels": [row[0] for row in rows],
                "datasets": [{
                    "data": [row[1] for row in rows],
                    "backgroundColor": [
                        "rgba(54, 162, 235, 0.5)",
                        "rgba(255, 99, 132, 0.5)",
                        "rgba(75, 192, 192, 0.5)"
                    ]
                }]
            }
        }
    
    async def process_casos_edad(self, filtros: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa datos para casos por grupos de edad
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
        WHERE 1=1
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
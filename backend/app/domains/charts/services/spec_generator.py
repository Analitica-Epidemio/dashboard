"""
Chart Spec Generator Service
Genera especificaciones universales de charts desde datos REALES de la BD
Reutiliza ChartDataProcessor para obtener los datos
"""

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.dashboard.processors import ChartDataProcessor
from app.domains.charts.schemas import (
    ConfiguracionGraficoArea,
    WrapperConfiguracionGraficoArea,
    DatosGraficoArea,
    ConfiguracionGraficoBarra,
    WrapperConfiguracionGraficoBarra,
    DatosGraficoBarra,
    DatosGraficoBase,
    FiltrosGrafico,
    ConjuntoDatos,
    ConfiguracionGraficoLinea,
    WrapperConfiguracionGraficoLinea,
    # Discriminated union wrappers
    DatosGraficoLinea,
    ConfiguracionGraficoMapa,
    WrapperConfiguracionGraficoMapa,
    DatosGraficoMapa,
    WrapperDatosGraficoMapa,
    DatosDepartamentoMapa,
    ConfiguracionGraficoTorta,
    WrapperConfiguracionGraficoTorta,
    DatosGraficoTorta,
    ConfiguracionGraficoPiramide,
    WrapperConfiguracionGraficoPiramide,
    DatosGraficoPiramide,
    PuntoDatosPiramide,
    EspecificacionGraficoUniversal,
    MetadataSemana,
)


class ChartSpecGenerator:
    """
    Generador de especificaciones universales de charts
    Usa ChartDataProcessor para obtener datos REALES de la BD
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.processor = ChartDataProcessor(db)

    async def generar_spec(
        self,
        codigo_grafico: str,
        filtros: FiltrosGrafico,
        configuracion: Optional[Dict[str, Any]] = None,
    ) -> EspecificacionGraficoUniversal:
        """
        Genera el spec universal para un chart dado con datos REALES
        """
        # Mapeo de códigos de charts a generadores
        generadores = {
            "curva_epidemiologica": self._generar_curva_epidemiologica,
            "corredor_endemico": self._generar_corredor_endemico,
            "piramide_edad": self._generar_piramide_edad,
            "mapa_chubut": self._generar_mapa_chubut,
            "estacionalidad": self._generar_estacionalidad,
            "casos_edad": self._generar_casos_edad,
            "distribucion_clasificacion": self._generar_distribucion_clasificacion,
            "casos_por_semana": self._generar_curva_epidemiologica,  # Alias
        }

        generador = generadores.get(codigo_grafico)
        if not generador:
            raise ValueError(f"Chart code '{codigo_grafico}' no reconocido")

        return await generador(filtros, configuracion)

    def _convertir_filtros_a_dict(self, filtros: FiltrosGrafico) -> Dict[str, Any]:
        """Convierte FiltrosGrafico a dict para ChartDataProcessor"""
        return {
            "grupo_id": filtros.ids_grupo_eno[0] if filtros.ids_grupo_eno and len(filtros.ids_grupo_eno) > 0 else None,
            "tipo_eno_ids": filtros.ids_tipo_eno,
            "clasificaciones": filtros.clasificacion,
            "provincia_id": filtros.id_provincia[0] if filtros.id_provincia and len(filtros.id_provincia) > 0 else None,
            "fecha_desde": filtros.fecha_desde,
            "fecha_hasta": filtros.fecha_hasta,
        }

    async def _generar_curva_epidemiologica(
        self,
        filtros: FiltrosGrafico,
        configuracion: Optional[Dict[str, Any]] = None,
        configuracion_series: Optional[List[Dict[str, Any]]] = None,
        agrupar_por: Optional[str] = None
    ) -> EspecificacionGraficoUniversal:
        """
        Genera spec para curva epidemiológica (casos por semana)
        Usa datos REALES del processor

        Args:
            filtros: Filtros de chart
            configuracion: Configuración de visualización
            configuracion_series: Config de series (si no se pasa, se construye desde filters.ids_tipo_eno)
            agrupar_por: "evento" | "agente" | None - cómo agrupar las series
        """
        filtros_dict = self._convertir_filtros_a_dict(filtros)

        # Construir configuracion_series si no se pasó
        if configuracion_series is None:
            ids_tipo_eno = filtros.ids_tipo_eno or []
            if ids_tipo_eno:
                configuracion_series = [
                    {"tipo_eno_id": id, "label": "Casos", "color": "rgb(75, 192, 192)"}
                    for id in ids_tipo_eno
                ]
            else:
                # Sin tipo_eno_ids, no hay series
                configuracion_series = []

        resultado = await self.processor.procesar_curva_epidemiologica(filtros_dict, configuracion_series, agrupar_por=agrupar_por)

        # Convertir resultado del processor al formato EspecificacionGraficoUniversal
        datos_crudos = resultado.get("data", {})

        # Convertir datasets al formato correcto
        conjuntos_datos = []
        for ds in datos_crudos.get("datasets", []):
            conjuntos_datos.append(
                ConjuntoDatos(
                    etiqueta=ds.get("label"),
                    datos=ds.get("data", []),
                    color=ds.get("borderColor"),
                    tipo=ds.get("type")  # "line" o "area"
                )
            )

        # Convertir metadata si existe
        metadata = None
        if datos_crudos.get("metadata"):
            metadata = [
                MetadataSemana(
                    anio=m["year"],
                    semana=m["week"],
                    fecha_inicio=m["start_date"],
                    fecha_fin=m["end_date"]
                ) for m in datos_crudos["metadata"]
            ]

        datos_base = DatosGraficoBase(
            etiquetas=datos_crudos.get("labels", []),
            conjuntos_datos=conjuntos_datos,
            metadata=metadata
        )

        # Determinar tipo de chart basado en config.chart_type
        tipo_grafico = configuracion.get("chart_type", "line") if configuracion else "line"
        es_apilado = tipo_grafico == "stacked_bar"
        es_barra = tipo_grafico in ("bar", "stacked_bar", "grouped_bar")

        if es_barra:
            # Renderizar como bar chart (stacked o no)
            config_barra = ConfiguracionGraficoBarra(
                alto=configuracion.get("height", 400) if configuracion else 400,
                mostrar_leyenda=True,
                mostrar_grilla=True,
                apilado=es_apilado,
            )
            return EspecificacionGraficoUniversal(
                id=str(uuid.uuid4()),
                titulo="Casos por Semana Epidemiológica",
                codigo="curva_epidemiologica",
                tipo="bar",
                datos=DatosGraficoBarra(tipo="bar", datos=datos_base),
                configuracion=WrapperConfiguracionGraficoBarra(tipo="bar", configuracion=config_barra),
                filtros=filtros,
            )
        else:
            # Renderizar como line chart (default)
            config_linea = ConfiguracionGraficoLinea(
                alto=configuracion.get("height", 400) if configuracion else 400,
                mostrar_leyenda=True,
                mostrar_grilla=True,
                mostrar_puntos=True,
            )
            return EspecificacionGraficoUniversal(
                id=str(uuid.uuid4()),
                titulo="Casos por Semana Epidemiológica",
                codigo="curva_epidemiologica",
                tipo="line",
                datos=DatosGraficoLinea(tipo="line", datos=datos_base),
                configuracion=WrapperConfiguracionGraficoLinea(tipo="line", configuracion=config_linea),
                filtros=filtros,
            )

    async def _generar_corredor_endemico(
        self, filtros: FiltrosGrafico, configuracion: Optional[Dict[str, Any]] = None
    ) -> EspecificacionGraficoUniversal:
        """
        Genera spec para corredor endémico
        Usa datos REALES del processor
        """
        from app.domains.charts.schemas import ErrorGrafico

        filtros_dict = self._convertir_filtros_a_dict(filtros)
        resultado = await self.processor.procesar_corredor_endemico(filtros_dict)

        datos_crudos = resultado.get("data", {})

        # Verificar si hay error del processor
        error_grafico = None
        if resultado.get("error"):
            datos_error = resultado["error"]
            error_grafico = ErrorGrafico(
                codigo=datos_error.get("code", "UNKNOWN_ERROR"),
                titulo=datos_error.get("title", "Error"),
                mensaje=datos_error.get("message", "No se pudo generar el gráfico"),
                detalles=datos_error.get("details"),
                sugerencia=datos_error.get("suggestion"),
            )

        conjuntos_datos = []
        for ds in datos_crudos.get("datasets", []):
            conjuntos_datos.append(
                ConjuntoDatos(
                    etiqueta=ds.get("label"),
                    datos=ds.get("data", []),
                    color=ds.get("color"),  # Usar "color" directamente
                    tipo=ds.get("type")  # No default - respetar el tipo del backend
                )
            )

        metadata = None
        if datos_crudos.get("metadata"):
            metadata = [
                MetadataSemana(
                    anio=m["year"],
                    semana=m["week"],
                    fecha_inicio=m["start_date"],
                    fecha_fin=m["end_date"]
                ) for m in datos_crudos["metadata"]
            ]

        datos_base = DatosGraficoBase(
            etiquetas=datos_crudos.get("labels", []),
            conjuntos_datos=conjuntos_datos,
            metadata=metadata
        )

        config_grafico = ConfiguracionGraficoArea(
            alto=configuracion.get("height", 400) if configuracion else 400,
            mostrar_leyenda=True,
            apilado=False,
            opacidad_relleno=0.2,
        )

        return EspecificacionGraficoUniversal(
            id=str(uuid.uuid4()),
            titulo="Corredor Endémico",
            codigo="corredor_endemico",
            tipo="area",
            datos=DatosGraficoArea(tipo="area", datos=datos_base),
            configuracion=WrapperConfiguracionGraficoArea(tipo="area", configuracion=config_grafico),
            filtros=filtros,
            error=error_grafico,
        )

    async def _generar_piramide_edad(
        self, filtros: FiltrosGrafico, configuracion: Optional[Dict[str, Any]] = None
    ) -> EspecificacionGraficoUniversal:
        """
        Genera spec para pirámide poblacional
        Usa datos REALES del processor
        """
        filtros_dict = self._convertir_filtros_a_dict(filtros)
        resultado = await self.processor.procesar_piramide_poblacional(filtros_dict)

        # El processor retorna formato diferente para pyramid
        # result["data"] es una lista de dicts con age, sex, value
        piramide_cruda = resultado.get("data", [])

        # El procesador ya retorna el formato correcto: [{ age_group, male, female }, ...]
        # Solo necesitamos convertir a PuntoDatosPiramide
        datos_piramide = [
            PuntoDatosPiramide(
                grupo_edad=item["age_group"],
                masculino=item["male"],
                femenino=item["female"]
            )
            for item in piramide_cruda
        ]

        config_grafico = ConfiguracionGraficoPiramide(
            alto=configuracion.get("height", 500) if configuracion else 500,
            mostrar_etiquetas_ejes=True,
        )

        return EspecificacionGraficoUniversal(
            id=str(uuid.uuid4()),
            titulo="Pirámide Poblacional por Edad y Sexo",
            codigo="piramide_edad",
            tipo="d3_pyramid",
            datos=DatosGraficoPiramide(tipo="d3_pyramid", datos=datos_piramide),
            configuracion=WrapperConfiguracionGraficoPiramide(tipo="d3_pyramid", configuracion=config_grafico),
            filtros=filtros,
        )

    async def _generar_mapa_chubut(
        self, filtros: FiltrosGrafico, configuracion: Optional[Dict[str, Any]] = None
    ) -> EspecificacionGraficoUniversal:
        """
        Genera spec para mapa de Chubut
        Usa datos REALES del processor
        """
        filtros_dict = self._convertir_filtros_a_dict(filtros)
        resultado = await self.processor.procesar_mapa_geografico(filtros_dict)

        # Convertir formato del processor al formato DatosGraficoMapa
        datos_crudos = resultado.get("data", {})

        departamentos = [
            DatosDepartamentoMapa(
                codigo_indec=dept["codigo_indec"],
                nombre=dept["nombre"],
                zona_ugd=dept["zona_ugd"],
                poblacion=dept["poblacion"],
                casos=dept["casos"],
                tasa_incidencia=dept["tasa_incidencia"]
            )
            for dept in datos_crudos.get("departamentos", [])
        ]

        datos_mapa = DatosGraficoMapa(
            departamentos=departamentos,
            total_casos=datos_crudos.get("total_casos", 0)
        )

        config_grafico = ConfiguracionGraficoMapa(
            alto=configuracion.get("height", 600) if configuracion else 600,
            provincia="chubut",
            escala_color="sequential",
        )

        return EspecificacionGraficoUniversal(
            id=str(uuid.uuid4()),
            titulo="Mapa de Casos - Chubut",
            codigo="mapa_chubut",
            tipo="mapa",
            datos=WrapperDatosGraficoMapa(tipo="mapa", datos=datos_mapa),
            configuracion=WrapperConfiguracionGraficoMapa(tipo="mapa", configuracion=config_grafico),
            filtros=filtros,
        )

    async def _generar_estacionalidad(
        self, filtros: FiltrosGrafico, configuracion: Optional[Dict[str, Any]] = None
    ) -> EspecificacionGraficoUniversal:
        """
        Genera spec para estacionalidad mensual
        Usa datos REALES del processor
        """
        filtros_dict = self._convertir_filtros_a_dict(filtros)
        resultado = await self.processor.procesar_estacionalidad(filtros_dict)

        datos_crudos = resultado.get("data", {})

        conjuntos_datos = []
        for ds in datos_crudos.get("datasets", []):
            conjuntos_datos.append(
                ConjuntoDatos(
                    etiqueta=ds.get("label"),
                    datos=ds.get("data", []),
                    color=ds.get("backgroundColor"),
                )
            )

        datos_base = DatosGraficoBase(
            etiquetas=datos_crudos.get("labels", []),
            conjuntos_datos=conjuntos_datos,
        )

        config_grafico = ConfiguracionGraficoBarra(
            alto=configuracion.get("height", 400) if configuracion else 400,
            mostrar_leyenda=False,
            mostrar_grilla=True,
        )

        return EspecificacionGraficoUniversal(
            id=str(uuid.uuid4()),
            titulo="Estacionalidad Mensual",
            codigo="estacionalidad",
            tipo="bar",
            datos=DatosGraficoBarra(tipo="bar", datos=datos_base),
            configuracion=WrapperConfiguracionGraficoBarra(tipo="bar", configuracion=config_grafico),
            filtros=filtros,
        )

    async def _generar_casos_por_edad(
        self,
        filtros: FiltrosGrafico,
        configuracion: Optional[Dict[str, Any]] = None,
        configuracion_series: Optional[List[Dict[str, Any]]] = None,
        agrupar_por: Optional[str] = None
    ) -> EspecificacionGraficoUniversal:
        """
        Genera spec para casos por grupo de edad (con soporte para múltiples series)
        Usa datos REALES del processor

        Args:
            filtros: Filtros de chart
            configuracion: Configuración de visualización
            configuracion_series: Config de series (si no se pasa, se construye desde filters.ids_tipo_eno)
            agrupar_por: "evento" | "agente" | None - cómo agrupar las series
        """
        filtros_dict = self._convertir_filtros_a_dict(filtros)

        # Construir configuracion_series si no se pasó
        if configuracion_series is None:
            ids_tipo_eno = filtros.ids_tipo_eno or []
            if ids_tipo_eno:
                configuracion_series = [
                    {"tipo_eno_id": id, "label": "Casos", "color": "#4CAF50"}
                    for id in ids_tipo_eno
                ]
            else:
                configuracion_series = []

        resultado = await self.processor.procesar_casos_edad(filtros_dict, series_config=configuracion_series, agrupar_por=agrupar_por)

        datos_crudos = resultado.get("data", {})

        conjuntos_datos = []
        for ds in datos_crudos.get("datasets", []):
            conjuntos_datos.append(
                ConjuntoDatos(
                    etiqueta=ds.get("label"),
                    datos=ds.get("data", []),
                    color=ds.get("backgroundColor") or ds.get("color"),
                )
            )

        datos_base = DatosGraficoBase(
            etiquetas=datos_crudos.get("labels", []),
            conjuntos_datos=conjuntos_datos,
        )

        # Mostrar leyenda si hay múltiples series
        mostrar_leyenda = len(conjuntos_datos) > 1

        # Determinar si debe ser stacked - puede venir como flag "stacked" o como chart_type "stacked_bar"
        es_apilado = False
        if configuracion:
            es_apilado = configuracion.get("stacked", False) or configuracion.get("chart_type") == "stacked_bar"

        config_grafico = ConfiguracionGraficoBarra(
            alto=configuracion.get("height", 400) if configuracion else 400,
            mostrar_leyenda=mostrar_leyenda,
            mostrar_grilla=True,
            apilado=es_apilado,
        )

        return EspecificacionGraficoUniversal(
            id=str(uuid.uuid4()),
            titulo="Casos por Grupo de Edad",
            codigo="casos_edad",
            tipo="bar",
            datos=DatosGraficoBarra(tipo="bar", datos=datos_base),
            configuracion=WrapperConfiguracionGraficoBarra(tipo="bar", configuracion=config_grafico),
            filtros=filtros,
        )

    async def _generar_casos_edad(
        self, filtros: FiltrosGrafico, configuracion: Optional[Dict[str, Any]] = None
    ) -> EspecificacionGraficoUniversal:
        """
        Genera spec para casos por grupo de edad (versión simple, sin series)
        Usa datos REALES del processor
        """
        return await self._generar_casos_por_edad(filtros, configuracion)

    async def _generar_distribucion_clasificacion(
        self, filtros: FiltrosGrafico, configuracion: Optional[Dict[str, Any]] = None
    ) -> EspecificacionGraficoUniversal:
        """
        Genera spec para distribución por clasificación
        Usa datos REALES del processor
        """
        filtros_dict = self._convertir_filtros_a_dict(filtros)
        resultado = await self.processor.procesar_distribucion_clasificacion(filtros_dict)

        datos_crudos = resultado.get("data", {})

        conjuntos_datos = []
        for ds in datos_crudos.get("datasets", []):
            conjuntos_datos.append(
                ConjuntoDatos(
                    etiqueta=ds.get("label", "Casos"),
                    datos=ds.get("data", []),
                    color=None,  # Pie chart usa backgroundColor del dataset
                )
            )

        datos_base = DatosGraficoBase(
            etiquetas=datos_crudos.get("labels", []),
            conjuntos_datos=conjuntos_datos,
        )

        config_grafico = ConfiguracionGraficoTorta(
            alto=configuracion.get("height", 400) if configuracion else 400,
            mostrar_leyenda=True,
            mostrar_porcentajes=True,
        )

        return EspecificacionGraficoUniversal(
            id=str(uuid.uuid4()),
            titulo="Distribución por Clasificación",
            codigo="distribucion_clasificacion",
            tipo="pie",
            datos=DatosGraficoTorta(tipo="pie", datos=datos_base),
            configuracion=WrapperConfiguracionGraficoTorta(tipo="pie", configuracion=config_grafico),
            filtros=filtros,
        )

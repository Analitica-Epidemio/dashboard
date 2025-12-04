"""
Chart Spec Generator Service
Genera especificaciones universales de charts desde datos REALES de la BD
Reutiliza ChartDataProcessor para obtener los datos
"""

import uuid
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.features.dashboard.processors import ChartDataProcessor
from app.schemas.chart_spec import (
    AreaChartConfig,
    AreaChartConfigWrapper,
    AreaChartData,
    BarChartConfig,
    BarChartConfigWrapper,
    BarChartData,
    BaseChartData,
    ChartFilters,
    Dataset,
    LineChartConfig,
    LineChartConfigWrapper,
    # Discriminated union wrappers
    LineChartData,
    MapChartConfig,
    MapChartConfigWrapper,
    MapChartData,
    MapChartDataWrapper,
    MapDepartmentData,
    PieChartConfig,
    PieChartConfigWrapper,
    PieChartData,
    PyramidChartConfig,
    PyramidChartConfigWrapper,
    PyramidChartData,
    PyramidDataPoint,
    UniversalChartSpec,
    WeekMetadata,
)


class ChartSpecGenerator:
    """
    Generador de especificaciones universales de charts
    Usa ChartDataProcessor para obtener datos REALES de la BD
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.processor = ChartDataProcessor(db)

    async def generate_spec(
        self,
        chart_code: str,
        filters: ChartFilters,
        config: Optional[Dict[str, Any]] = None,
    ) -> UniversalChartSpec:
        """
        Genera el spec universal para un chart dado con datos REALES
        """
        # Mapeo de códigos de charts a generadores
        generators = {
            "casos_por_semana": self._generate_casos_por_semana,
            "corredor_endemico": self._generate_corredor_endemico,
            "piramide_edad": self._generate_piramide_edad,
            "mapa_chubut": self._generate_mapa_chubut,
            "estacionalidad": self._generate_estacionalidad,
            "casos_edad": self._generate_casos_edad,
            "distribucion_clasificacion": self._generate_distribucion_clasificacion,
            # Agregar más charts según sea necesario
        }

        generator = generators.get(chart_code)
        if not generator:
            raise ValueError(f"Chart code '{chart_code}' no reconocido")

        return await generator(filters, config)

    def _convert_filters_to_dict(self, filters: ChartFilters) -> Dict[str, Any]:
        """Convierte ChartFilters a dict para ChartDataProcessor"""
        return {
            "grupo_id": filters.grupo_eno_ids[0] if filters.grupo_eno_ids and len(filters.grupo_eno_ids) > 0 else None,
            "tipo_eno_ids": filters.tipo_eno_ids,
            "clasificaciones": filters.clasificacion,
            "provincia_id": filters.provincia_id[0] if filters.provincia_id and len(filters.provincia_id) > 0 else None,
            "fecha_desde": filters.fecha_desde,
            "fecha_hasta": filters.fecha_hasta,
        }

    async def _generate_casos_por_semana(
        self, filters: ChartFilters, config: Optional[Dict[str, Any]] = None
    ) -> UniversalChartSpec:
        """
        Genera spec para curva epidemiológica (casos por semana)
        Usa datos REALES del processor
        """
        # Convertir filtros y obtener datos reales
        filtros_dict = self._convert_filters_to_dict(filters)
        result = await self.processor.process_curva_epidemiologica(filtros_dict)

        # Convertir resultado del processor al formato UniversalChartSpec
        raw_data = result.get("data", {})

        # Convertir datasets al formato correcto
        datasets = []
        for ds in raw_data.get("datasets", []):
            datasets.append(
                Dataset(
                    label=ds.get("label"),
                    data=ds.get("data", []),
                    color=ds.get("borderColor"),
                    type=ds.get("type")  # "line" o "area"
                )
            )

        # Convertir metadata si existe
        metadata = None
        if raw_data.get("metadata"):
            metadata = [
                WeekMetadata(**m) for m in raw_data["metadata"]
            ]

        base_data = BaseChartData(
            labels=raw_data.get("labels", []),
            datasets=datasets,
            metadata=metadata
        )

        chart_config = LineChartConfig(
            height=config.get("height", 400) if config else 400,
            showLegend=True,
            showGrid=True,
            showPoints=True,
        )

        return UniversalChartSpec(
            id=str(uuid.uuid4()),
            title="Casos por Semana Epidemiológica",
            codigo="casos_por_semana",
            type="line",
            data=LineChartData(type="line", data=base_data),
            config=LineChartConfigWrapper(type="line", config=chart_config),
            filters=filters,
        )

    async def _generate_corredor_endemico(
        self, filters: ChartFilters, config: Optional[Dict[str, Any]] = None
    ) -> UniversalChartSpec:
        """
        Genera spec para corredor endémico
        Usa datos REALES del processor
        """
        filtros_dict = self._convert_filters_to_dict(filters)
        result = await self.processor.process_corredor_endemico(filtros_dict)

        raw_data = result.get("data", {})

        datasets = []
        for ds in raw_data.get("datasets", []):
            datasets.append(
                Dataset(
                    label=ds.get("label"),
                    data=ds.get("data", []),
                    color=ds.get("color"),  # Usar "color" directamente
                    type=ds.get("type")  # No default - respetar el tipo del backend
                )
            )

        metadata = None
        if raw_data.get("metadata"):
            metadata = [WeekMetadata(**m) for m in raw_data["metadata"]]

        base_data = BaseChartData(
            labels=raw_data.get("labels", []),
            datasets=datasets,
            metadata=metadata
        )

        chart_config = AreaChartConfig(
            height=config.get("height", 400) if config else 400,
            showLegend=True,
            stacked=False,
            fillOpacity=0.2,
        )

        return UniversalChartSpec(
            id=str(uuid.uuid4()),
            title="Corredor Endémico",
            codigo="corredor_endemico",
            type="area",
            data=AreaChartData(type="area", data=base_data),
            config=AreaChartConfigWrapper(type="area", config=chart_config),
            filters=filters,
        )

    async def _generate_piramide_edad(
        self, filters: ChartFilters, config: Optional[Dict[str, Any]] = None
    ) -> UniversalChartSpec:
        """
        Genera spec para pirámide poblacional
        Usa datos REALES del processor
        """
        filtros_dict = self._convert_filters_to_dict(filters)
        result = await self.processor.process_piramide_poblacional(filtros_dict)

        # El processor retorna formato diferente para pyramid
        # result["data"] es una lista de dicts con age, sex, value
        pyramid_raw = result.get("data", [])

        # El procesador ya retorna el formato correcto: [{ age_group, male, female }, ...]
        # Solo necesitamos convertir a PyramidDataPoint
        pyramid_data = [
            PyramidDataPoint(
                age_group=item["age_group"],
                male=item["male"],
                female=item["female"]
            )
            for item in pyramid_raw
        ]

        chart_config = PyramidChartConfig(
            height=config.get("height", 500) if config else 500,
            showAxisLabels=True,
        )

        return UniversalChartSpec(
            id=str(uuid.uuid4()),
            title="Pirámide Poblacional por Edad y Sexo",
            codigo="piramide_edad",
            type="d3_pyramid",
            data=PyramidChartData(type="d3_pyramid", data=pyramid_data),
            config=PyramidChartConfigWrapper(type="d3_pyramid", config=chart_config),
            filters=filters,
        )

    async def _generate_mapa_chubut(
        self, filters: ChartFilters, config: Optional[Dict[str, Any]] = None
    ) -> UniversalChartSpec:
        """
        Genera spec para mapa de Chubut
        Usa datos REALES del processor
        """
        filtros_dict = self._convert_filters_to_dict(filters)
        result = await self.processor.process_mapa_geografico(filtros_dict)

        # Convertir formato del processor al formato MapChartData
        raw_data = result.get("data", {})

        departamentos = [
            MapDepartmentData(**dept)
            for dept in raw_data.get("departamentos", [])
        ]

        map_data = MapChartData(
            departamentos=departamentos,
            total_casos=raw_data.get("total_casos", 0)
        )

        chart_config = MapChartConfig(
            height=config.get("height", 600) if config else 600,
            province="chubut",
            colorScale="sequential",
        )

        return UniversalChartSpec(
            id=str(uuid.uuid4()),
            title="Mapa de Casos - Chubut",
            codigo="mapa_chubut",
            type="mapa",
            data=MapChartDataWrapper(type="mapa", data=map_data),
            config=MapChartConfigWrapper(type="mapa", config=chart_config),
            filters=filters,
        )

    async def _generate_estacionalidad(
        self, filters: ChartFilters, config: Optional[Dict[str, Any]] = None
    ) -> UniversalChartSpec:
        """
        Genera spec para estacionalidad mensual
        Usa datos REALES del processor
        """
        filtros_dict = self._convert_filters_to_dict(filters)
        result = await self.processor.process_estacionalidad(filtros_dict)

        raw_data = result.get("data", {})

        datasets = []
        for ds in raw_data.get("datasets", []):
            datasets.append(
                Dataset(
                    label=ds.get("label"),
                    data=ds.get("data", []),
                    color=ds.get("backgroundColor"),
                )
            )

        base_data = BaseChartData(
            labels=raw_data.get("labels", []),
            datasets=datasets,
        )

        chart_config = BarChartConfig(
            height=config.get("height", 400) if config else 400,
            showLegend=False,
            showGrid=True,
        )

        return UniversalChartSpec(
            id=str(uuid.uuid4()),
            title="Estacionalidad Mensual",
            codigo="estacionalidad",
            type="bar",
            data=BarChartData(type="bar", data=base_data),
            config=BarChartConfigWrapper(type="bar", config=chart_config),
            filters=filters,
        )

    async def _generate_casos_edad(
        self, filters: ChartFilters, config: Optional[Dict[str, Any]] = None
    ) -> UniversalChartSpec:
        """
        Genera spec para casos por grupo de edad
        Usa datos REALES del processor
        """
        filtros_dict = self._convert_filters_to_dict(filters)
        result = await self.processor.process_casos_edad(filtros_dict)

        raw_data = result.get("data", {})

        datasets = []
        for ds in raw_data.get("datasets", []):
            datasets.append(
                Dataset(
                    label=ds.get("label"),
                    data=ds.get("data", []),
                    color=ds.get("backgroundColor"),
                )
            )

        base_data = BaseChartData(
            labels=raw_data.get("labels", []),
            datasets=datasets,
        )

        chart_config = BarChartConfig(
            height=config.get("height", 400) if config else 400,
            showLegend=False,
            showGrid=True,
        )

        return UniversalChartSpec(
            id=str(uuid.uuid4()),
            title="Casos por Grupo de Edad",
            codigo="casos_edad",
            type="bar",
            data=BarChartData(type="bar", data=base_data),
            config=BarChartConfigWrapper(type="bar", config=chart_config),
            filters=filters,
        )

    async def _generate_distribucion_clasificacion(
        self, filters: ChartFilters, config: Optional[Dict[str, Any]] = None
    ) -> UniversalChartSpec:
        """
        Genera spec para distribución por clasificación
        Usa datos REALES del processor
        """
        filtros_dict = self._convert_filters_to_dict(filters)
        result = await self.processor.process_distribucion_clasificacion(filtros_dict)

        raw_data = result.get("data", {})

        datasets = []
        for ds in raw_data.get("datasets", []):
            datasets.append(
                Dataset(
                    label=ds.get("label", "Casos"),
                    data=ds.get("data", []),
                    color=None,  # Pie chart usa backgroundColor del dataset
                )
            )

        base_data = BaseChartData(
            labels=raw_data.get("labels", []),
            datasets=datasets,
        )

        chart_config = PieChartConfig(
            height=config.get("height", 400) if config else 400,
            showLegend=True,
            showPercentages=True,
        )

        return UniversalChartSpec(
            id=str(uuid.uuid4()),
            title="Distribución por Clasificación",
            codigo="distribucion_clasificacion",
            type="pie",
            data=PieChartData(type="pie", data=base_data),
            config=PieChartConfigWrapper(type="pie", config=chart_config),
            filters=filters,
        )

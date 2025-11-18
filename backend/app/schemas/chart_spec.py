"""
Universal Chart Specification
Schemas Pydantic para la especificación universal de charts
Compatibles con los tipos TypeScript del frontend
"""

from typing import List, Optional, Dict, Any, Literal, Union, Annotated
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# Tipos Base
# ============================================================================

ChartType = Literal["line", "bar", "area", "pie", "d3_pyramid", "mapa"]


class WeekMetadata(BaseModel):
    """Metadata de semana epidemiológica"""
    year: int
    week: int
    start_date: str
    end_date: str


class Dataset(BaseModel):
    """Dataset para charts line/bar/area/pie"""
    label: Optional[str] = None
    data: List[float]
    color: Optional[str] = None
    type: Optional[Literal["area", "line"]] = None  # Para area charts con líneas


# ============================================================================
# Datos por Tipo de Chart
# ============================================================================

class BaseChartData(BaseModel):
    """Datos para line, bar, area, pie charts"""
    labels: List[str]
    datasets: List[Dataset]
    metadata: Optional[List[WeekMetadata]] = None


class PyramidDataPoint(BaseModel):
    """Punto de datos para pirámide poblacional"""
    age_group: str
    male: float
    female: float


class MapDepartmentData(BaseModel):
    """Datos de departamento para mapa"""
    codigo_indec: int
    nombre: str
    zona_ugd: str
    poblacion: int
    casos: int
    tasa_incidencia: float


class MapChartData(BaseModel):
    """Datos para mapa de Chubut"""
    departamentos: List[MapDepartmentData]
    total_casos: int


# ============================================================================
# Discriminated Union Wrappers para Data
# ============================================================================

class LineChartData(BaseModel):
    """Wrapper con discriminador para line chart data"""
    type: Literal["line"] = "line"
    data: BaseChartData


class BarChartData(BaseModel):
    """Wrapper con discriminador para bar chart data"""
    type: Literal["bar"] = "bar"
    data: BaseChartData


class AreaChartData(BaseModel):
    """Wrapper con discriminador para area chart data"""
    type: Literal["area"] = "area"
    data: BaseChartData


class PieChartData(BaseModel):
    """Wrapper con discriminador para pie chart data"""
    type: Literal["pie"] = "pie"
    data: BaseChartData


class PyramidChartData(BaseModel):
    """Wrapper con discriminador para pyramid chart data"""
    type: Literal["d3_pyramid"] = "d3_pyramid"
    data: List[PyramidDataPoint]


class MapChartDataWrapper(BaseModel):
    """Wrapper con discriminador para map chart data"""
    type: Literal["mapa"] = "mapa"
    data: MapChartData


# Union discriminada para todos los tipos de datos
ChartDataUnion = Annotated[
    Union[
        LineChartData,
        BarChartData,
        AreaChartData,
        PieChartData,
        PyramidChartData,
        MapChartDataWrapper,
    ],
    Field(discriminator="type"),
]


# ============================================================================
# Configuración de Charts
# ============================================================================

class BaseChartConfig(BaseModel):
    """Configuración base para todos los charts"""
    height: Optional[int] = None
    width: Optional[int] = None
    showLegend: Optional[bool] = True
    showGrid: Optional[bool] = True
    colors: Optional[List[str]] = None


class LineChartConfig(BaseChartConfig):
    """Configuración específica para line charts"""
    showPoints: Optional[bool] = True
    curved: Optional[bool] = False


class BarChartConfig(BaseChartConfig):
    """Configuración específica para bar charts"""
    stacked: Optional[bool] = False
    horizontal: Optional[bool] = False


class AreaChartConfig(BaseChartConfig):
    """Configuración específica para area charts"""
    stacked: Optional[bool] = False
    fillOpacity: Optional[float] = 0.6


class PieChartConfig(BaseChartConfig):
    """Configuración específica para pie charts"""
    showPercentages: Optional[bool] = True
    innerRadius: Optional[int] = 0  # For donut charts


class PyramidChartConfig(BaseChartConfig):
    """Configuración específica para pyramid charts"""
    showAxisLabels: Optional[bool] = True


class MapChartConfig(BaseChartConfig):
    """Configuración específica para map charts"""
    colorScale: Optional[Literal["sequential", "diverging"]] = "sequential"
    province: Optional[Literal["chubut"]] = "chubut"


# ============================================================================
# Discriminated Union Wrappers para Config
# ============================================================================

class LineChartConfigWrapper(BaseModel):
    """Wrapper con discriminador para line chart config"""
    type: Literal["line"] = "line"
    config: LineChartConfig


class BarChartConfigWrapper(BaseModel):
    """Wrapper con discriminador para bar chart config"""
    type: Literal["bar"] = "bar"
    config: BarChartConfig


class AreaChartConfigWrapper(BaseModel):
    """Wrapper con discriminador para area chart config"""
    type: Literal["area"] = "area"
    config: AreaChartConfig


class PieChartConfigWrapper(BaseModel):
    """Wrapper con discriminador para pie chart config"""
    type: Literal["pie"] = "pie"
    config: PieChartConfig


class PyramidChartConfigWrapper(BaseModel):
    """Wrapper con discriminador para pyramid chart config"""
    type: Literal["d3_pyramid"] = "d3_pyramid"
    config: PyramidChartConfig


class MapChartConfigWrapper(BaseModel):
    """Wrapper con discriminador para map chart config"""
    type: Literal["mapa"] = "mapa"
    config: MapChartConfig


# Union discriminada para todos los tipos de config
ChartConfigUnion = Annotated[
    Union[
        LineChartConfigWrapper,
        BarChartConfigWrapper,
        AreaChartConfigWrapper,
        PieChartConfigWrapper,
        PyramidChartConfigWrapper,
        MapChartConfigWrapper,
    ],
    Field(discriminator="type"),
]


# ============================================================================
# Filtros (para reproducibilidad)
# ============================================================================

class ChartFilters(BaseModel):
    """Filtros aplicados al chart (para reproducibilidad)"""
    grupo_eno_ids: Optional[List[int]] = None
    tipo_eno_ids: Optional[List[int]] = None
    clasificacion: Optional[List[str]] = None
    provincia_id: Optional[List[int]] = None
    fecha_desde: Optional[str] = None
    fecha_hasta: Optional[str] = None
    edad_min: Optional[int] = None
    edad_max: Optional[int] = None
    tipo_sujeto: Optional[Literal["humano", "animal"]] = None
    extra: Optional[Dict[str, Any]] = Field(default_factory=dict)


# ============================================================================
# Especificación Universal
# ============================================================================

class UniversalChartSpec(BaseModel):
    """
    Especificación universal de chart
    Puede ser usada tanto por frontend como backend
    """
    # Metadata
    id: str
    title: str
    description: Optional[str] = None
    codigo: Optional[str] = None

    # Tipo de chart
    type: ChartType

    # Datos (con discriminador type para TypeScript)
    data: ChartDataUnion

    # Config (con discriminador type para TypeScript)
    config: ChartConfigUnion

    # Filtros aplicados (para reproducibilidad)
    filters: Optional[ChartFilters] = None

    # Timestamp
    generated_at: Optional[str] = Field(
        default_factory=lambda: datetime.now().isoformat()
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "chart_001",
                "title": "Casos por Semana Epidemiológica",
                "type": "line",
                "data": {
                    "labels": ["SE 1", "SE 2", "SE 3"],
                    "datasets": [
                        {"label": "Confirmados", "data": [10, 15, 12]},
                    ],
                },
                "config": {"height": 400, "showLegend": True},
            }
        }


# ============================================================================
# Request/Response para API
# ============================================================================

class ChartSpecRequest(BaseModel):
    """Request para obtener spec de un chart"""
    chart_code: str
    filters: ChartFilters
    config: Optional[Dict[str, Any]] = None


class ChartSpecResponse(BaseModel):
    """Response con el spec generado"""
    spec: UniversalChartSpec
    generated_at: str

"""
Schemas para la arquitectura Browse-First de charts
Simplificados y enfocados en UX
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChartVisualizationType(str, Enum):
    """Tipos de visualización disponibles"""
    LINE = "LINE"
    BAR = "BAR"
    PIE = "PIE"
    AREA = "AREA"
    SCATTER = "SCATTER"
    HEATMAP = "HEATMAP"
    MAP = "MAP"
    TABLE = "TABLE"
    METRIC = "METRIC"

class ChartCategory(str, Enum):
    """Categorías de charts"""
    EPIDEMIOLOGICAL = "EPIDEMIOLOGICAL"
    DEMOGRAPHIC = "DEMOGRAPHIC"
    GEOGRAPHIC = "GEOGRAPHIC"
    TEMPORAL = "TEMPORAL"
    COMPARATIVE = "COMPARATIVE"
    GENERAL = "GENERAL"

class FilterType(str, Enum):
    """Tipos de filtros disponibles"""
    DATE_RANGE = "DATE_RANGE"
    SINGLE_SELECT = "SINGLE_SELECT"
    MULTI_SELECT = "MULTI_SELECT"
    NUMBER_RANGE = "NUMBER_RANGE"
    TEXT_INPUT = "TEXT_INPUT"
    BOOLEAN = "BOOLEAN"
    ENO_SELECTOR = "ENO_SELECTOR"
    DEPARTMENT_SELECTOR = "DEPARTMENT_SELECTOR"

# ====== RESPONSES PRINCIPALES ======

class ChartTemplateResponse(BaseModel):
    """Template de chart para browse-first UI"""
    id: int
    codigo: str
    nombre: str
    descripcion: Optional[str]
    categoria: str
    tipo_visualizacion: ChartVisualizationType

    # Capacidades dinámicas
    tipo_eno_compatible: Optional[List[str]] = None  # null = todos
    filtros_requeridos: List[str] = Field(default_factory=list)
    filtros_opcionales: List[str] = Field(default_factory=list)
    parametros_disponibles: Dict[str, Any] = Field(default_factory=dict)
    parametros_default: Dict[str, Any] = Field(default_factory=dict)

    # UI metadata
    orden_sugerido: int = 0
    es_publico: bool = True
    requiere_autenticacion: bool = False

    # Timestamps
    created_at: datetime
    updated_at: datetime

class ChartDataResponse(BaseModel):
    """Datos de un chart ejecutado"""
    id_grafico: int
    codigo_grafico: str
    titulo: str
    descripcion: Optional[str] = None
    tipo_visualizacion: ChartVisualizationType

    # Datos principales
    data: Dict[str, Any]
    configuracion_chart: Dict[str, Any] = Field(default_factory=dict)

    # Metadatos
    filtros_aplicados: Dict[str, Any] = Field(default_factory=dict)
    parametros_aplicados: Dict[str, Any] = Field(default_factory=dict)
    timestamp_generacion: datetime
    tiempo_ejecucion_ms: Optional[int] = None

    # Info de datos
    total_registros: Optional[int] = None
    registros_filtrados: Optional[int] = None
    mensaje: Optional[str] = None

class FilterDefinitionResponse(BaseModel):
    """Definición de un filtro disponible"""
    codigo: str
    nombre: str
    descripcion: Optional[str]
    tipo_filtro: FilterType
    configuracion: Dict[str, Any] = Field(default_factory=dict)
    valor_default: Optional[Any] = None
    es_requerido: bool = False
    opciones: Optional[List[Dict[str, Any]]] = None


# ====== REQUESTS ======

class ExecuteChartRequest(BaseModel):
    """Request para ejecutar un chart"""
    codigo_grafico: str
    filtros: Dict[str, Any] = Field(default_factory=dict)
    parametros: Dict[str, Any] = Field(default_factory=dict)
    usar_cache: bool = True
    formato_respuesta: str = Field(default="json")


class ChartPreviewRequest(BaseModel):
    """Request para vista previa de chart"""
    codigo_grafico: str
    filtros: Dict[str, Any] = Field(default_factory=dict)
    parametros: Dict[str, Any] = Field(default_factory=dict)
    usar_datos_muestra: bool = True
    limite_registros: int = Field(default=100, ge=10, le=1000)

# ====== DASHBOARD Y LAYOUTS ======

class DashboardChartItem(BaseModel):
    """Item de chart en dashboard"""
    codigo_grafico: str
    titulo_personalizado: Optional[str] = None
    filtros_aplicados: Dict[str, Any] = Field(default_factory=dict)
    parametros_aplicados: Dict[str, Any] = Field(default_factory=dict)

    # Layout position
    posicion_x: int = 0
    posicion_y: int = 0
    ancho: int = 6  # grid columns (12 total)
    alto: int = 4   # grid rows

    # Display options
    mostrar_titulo: bool = True
    mostrar_controles: bool = True

class DashboardLayoutRequest(BaseModel):
    """Request para crear/actualizar dashboard"""
    nombre: str
    descripcion: Optional[str] = None
    charts: List[DashboardChartItem]
    filtros_globales: Dict[str, Any] = Field(default_factory=dict)
    es_publico: bool = False

class ChartAvailabilityResponse(BaseModel):
    """Disponibilidad de charts para un contexto específico"""
    total_graficos: int
    graficos_disponibles: List[ChartTemplateResponse]
    filtros_disponibles: List[FilterDefinitionResponse]

class ExportConfigRequest(BaseModel):
    """Request para exportar configuraciones"""
    incluir_templates: bool = True
    incluir_preferencias_usuario: bool = False
    formato: str = Field(default="json")
    codigos_graficos: Optional[List[str]] = None

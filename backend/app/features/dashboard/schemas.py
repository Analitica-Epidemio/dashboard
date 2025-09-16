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
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    MAP = "map"
    TABLE = "table"
    METRIC = "metric"

class ChartCategory(str, Enum):
    """Categorías de charts"""
    EPIDEMIOLOGICAL = "epidemiological"
    DEMOGRAPHIC = "demographic"
    GEOGRAPHIC = "geographic"
    TEMPORAL = "temporal"
    COMPARATIVE = "comparative"
    GENERAL = "general"

class FilterType(str, Enum):
    """Tipos de filtros disponibles"""
    DATE_RANGE = "date_range"
    SINGLE_SELECT = "single_select"
    MULTI_SELECT = "multi_select"
    NUMBER_RANGE = "number_range"
    TEXT_INPUT = "text_input"
    BOOLEAN = "boolean"
    ENO_SELECTOR = "eno_selector"
    DEPARTMENT_SELECTOR = "department_selector"

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
    chart_id: int
    chart_codigo: str
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
    chart_codigo: str
    filtros: Dict[str, Any] = Field(default_factory=dict)
    parametros: Dict[str, Any] = Field(default_factory=dict)
    usar_cache: bool = True
    formato_respuesta: str = Field(default="json")


class ChartPreviewRequest(BaseModel):
    """Request para vista previa de chart"""
    chart_codigo: str
    filtros: Dict[str, Any] = Field(default_factory=dict)
    parametros: Dict[str, Any] = Field(default_factory=dict)
    usar_datos_muestra: bool = True
    limite_registros: int = Field(default=100, ge=10, le=1000)

# ====== DASHBOARD Y LAYOUTS ======

class DashboardChartItem(BaseModel):
    """Item de chart en dashboard"""
    chart_codigo: str
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
    total_charts: int
    charts_disponibles: List[ChartTemplateResponse]
    filtros_disponibles: List[FilterDefinitionResponse]

class ExportConfigRequest(BaseModel):
    """Request para exportar configuraciones"""
    incluir_templates: bool = True
    incluir_preferencias_usuario: bool = False
    formato: str = Field(default="json")
    chart_codigos: Optional[List[str]] = None
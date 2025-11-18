"""
Schemas Pydantic para el sistema de boletines
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union, Annotated

from pydantic import BaseModel, Field, Discriminator


# ============================================================================
# Schemas de Configuración de Widgets
# ============================================================================

class WidgetPosition(BaseModel):
    """Posición del widget en el grid"""
    x: int = Field(..., ge=0, description="Posición X en el grid (columnas)")
    y: int = Field(..., ge=0, description="Posición Y en el grid (filas)")
    w: int = Field(..., ge=1, le=12, description="Ancho en columnas (1-12)")
    h: int = Field(..., ge=1, description="Alto en filas")


class KPIComparisonData(BaseModel):
    """Datos de comparación para KPI"""
    value: float = Field(..., description="Valor de la comparación (%)")
    trend: Literal["up", "down", "neutral"] = Field(..., description="Tendencia")


class KPIManualData(BaseModel):
    """Datos manuales para widget KPI"""
    value: float = Field(..., description="Valor principal del KPI")
    label: Optional[str] = Field(None, description="Etiqueta del KPI")
    comparison: Optional[KPIComparisonData] = Field(None, description="Datos de comparación")


class KPIDataConfig(BaseModel):
    """Configuración de datos para widget KPI"""
    source: Literal["manual", "query"] = Field(..., description="Fuente de datos")
    query_id: Optional[str] = Field(None, description="ID de la query si source=query")
    query_params: Optional[Dict[str, Any]] = Field(None, description="Parámetros de la query")
    manual_data: Optional[KPIManualData] = Field(None, description="Datos manuales para KPI")


class GenericDataConfig(BaseModel):
    """Configuración de datos genérica para otros widgets"""
    source: Literal["manual", "query"] = Field(..., description="Fuente de datos")
    query_id: Optional[str] = Field(None, description="ID de la query si source=query")
    query_params: Optional[Dict[str, Any]] = Field(None, description="Parámetros de la query")
    manual_data: Optional[Dict[str, Any]] = Field(None, description="Datos manuales")


# Para compatibilidad con código existente
WidgetDataConfig = KPIDataConfig | GenericDataConfig


class WidgetVisualConfig(BaseModel):
    """Configuración visual del widget"""
    show_title: bool = Field(True, description="Mostrar título")
    show_description: bool = Field(False, description="Mostrar descripción")
    # Configuraciones específicas por tipo de widget (flexibles)
    config: Optional[Dict[str, Any]] = Field(None, description="Configuración específica del tipo")


class KPIWidget(BaseModel):
    """Widget de KPI"""
    id: str = Field(..., description="ID único del widget")
    type: Literal["kpi"] = Field("kpi", description="Tipo de widget")
    position: WidgetPosition = Field(..., description="Posición en el grid")
    data_config: KPIDataConfig = Field(..., description="Configuración de datos para KPI")
    visual_config: WidgetVisualConfig = Field(..., description="Configuración visual")
    title: Optional[str] = Field(None, description="Título del widget")
    description: Optional[str] = Field(None, description="Descripción del widget")


class GenericWidget(BaseModel):
    """Widget genérico (table, chart, etc)"""
    id: str = Field(..., description="ID único del widget")
    type: Literal[
        "table", "line", "bar", "pie", "map",
        "pyramid", "corridor", "text", "image", "divider", "pagebreak"
    ] = Field(..., description="Tipo de widget")
    position: WidgetPosition = Field(..., description="Posición en el grid")
    data_config: GenericDataConfig = Field(..., description="Configuración de datos")
    visual_config: WidgetVisualConfig = Field(..., description="Configuración visual")
    title: Optional[str] = Field(None, description="Título del widget")
    description: Optional[str] = Field(None, description="Descripción del widget")


# Union type para todos los widgets (discriminated union por 'type')
Widget = Annotated[
    Union[KPIWidget, GenericWidget],
    Discriminator('type')
]


# ============================================================================
# Schemas de Layout y Portada
# ============================================================================

class LayoutConfig(BaseModel):
    """Configuración del layout del boletín"""
    type: Literal["grid"] = Field("grid", description="Tipo de layout")
    columns: int = Field(12, ge=1, le=24, description="Número de columnas")
    row_height: int = Field(40, ge=10, description="Alto de fila en pixels")
    margin: List[int] = Field([10, 10], description="Margen [horizontal, vertical]")


class CoverConfig(BaseModel):
    """Configuración de la portada"""
    enabled: bool = Field(True, description="Mostrar portada")
    title: str = Field(..., description="Título del boletín")
    subtitle: Optional[str] = Field(None, description="Subtítulo")
    logo: Optional[str] = Field(None, description="URL o path al logo")
    background_image: Optional[str] = Field(None, description="Imagen de fondo")
    footer: Optional[str] = Field(None, description="Texto del pie de página")


class GlobalFilters(BaseModel):
    """Filtros globales del boletín"""
    temporal: Optional[Dict[str, Any]] = Field(None, description="Filtros temporales")
    geografico: Optional[Dict[str, Any]] = Field(None, description="Filtros geográficos")
    demografico: Optional[Dict[str, Any]] = Field(None, description="Filtros demográficos")


# ============================================================================
# Schemas de Templates
# ============================================================================

class BoletinTemplateCreate(BaseModel):
    """Schema para crear template"""
    name: str = Field(..., min_length=1, max_length=255, description="Nombre del template")
    description: Optional[str] = Field(None, description="Descripción")
    category: str = Field(..., description="Categoría: semanal, brote, tendencias, etc.")
    thumbnail: Optional[str] = Field(None, description="URL de thumbnail")
    layout: LayoutConfig = Field(..., description="Configuración de layout")
    cover: Optional[CoverConfig] = Field(None, description="Configuración de portada")
    widgets: List[Widget] = Field([], description="Lista de widgets")
    global_filters: Optional[GlobalFilters] = Field(None, description="Filtros globales")
    content: Optional[str] = Field(None, description="Contenido HTML del boletín (Tiptap)")
    is_public: bool = Field(False, description="Template público")


class BoletinTemplateUpdate(BaseModel):
    """Schema para actualizar template"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    thumbnail: Optional[str] = None
    layout: Optional[LayoutConfig] = None
    cover: Optional[CoverConfig] = None
    widgets: Optional[List[Widget]] = None
    global_filters: Optional[GlobalFilters] = None
    content: Optional[str] = None
    is_public: Optional[bool] = None


class BoletinTemplateResponse(BaseModel):
    """Schema de respuesta de template"""
    id: int
    name: str
    description: Optional[str]
    category: str
    thumbnail: Optional[str]
    layout: LayoutConfig
    cover: Optional[CoverConfig]
    widgets: List[Widget]
    global_filters: Optional[GlobalFilters]
    content: Optional[str]
    created_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    is_public: bool
    is_system: bool

    class Config:
        from_attributes = True


# ============================================================================
# Schemas de Instancias (Boletines Generados)
# ============================================================================

class BoletinGenerateRequest(BaseModel):
    """Request para generar un boletín"""
    template_id: int = Field(..., description="ID del template a usar")
    name: str = Field(..., min_length=1, max_length=255, description="Nombre del boletín")
    parameters: Dict[str, Any] = Field(..., description="Parámetros específicos")


class BoletinInstanceResponse(BaseModel):
    """Schema de respuesta de instancia"""
    id: int
    template_id: Optional[int]
    name: str
    parameters: Dict[str, Any]
    content: Optional[str]
    pdf_path: Optional[str]
    pdf_size: Optional[int]  # Debe coincidir con el nombre del campo en el modelo
    status: str
    error_message: Optional[str]
    generated_by: Optional[int]
    generated_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Schemas de Query Definitions
# ============================================================================

class QueryDefinitionCreate(BaseModel):
    """Schema para crear query definition"""
    id: str = Field(..., description="ID único de la query")
    name: str = Field(..., description="Nombre descriptivo")
    description: Optional[str] = None
    category: str = Field(..., description="Categoría de la query")
    parameters_schema: Dict[str, Any] = Field(..., description="JSON Schema de parámetros")
    endpoint: str = Field(..., description="Endpoint que ejecuta la query")
    output_schema: Optional[Dict[str, Any]] = None
    example_params: Optional[Dict[str, Any]] = None
    example_output: Optional[Dict[str, Any]] = None


class QueryDefinitionResponse(BaseModel):
    """Schema de respuesta de query definition"""
    id: str
    name: str
    description: Optional[str]
    category: str
    parameters_schema: Dict[str, Any]
    endpoint: str
    output_schema: Optional[Dict[str, Any]]
    example_params: Optional[Dict[str, Any]]
    example_output: Optional[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================================================
# Schemas de Queries Epidemiológicas (Responses)
# ============================================================================

class TopEnoItem(BaseModel):
    """Item en la lista de top ENOs"""
    evento: str
    n_casos: int
    tasa_por_100k: Optional[float] = None


class CorredorEndemicoResponse(BaseModel):
    """Respuesta del corredor endémico"""
    semanas: List[int]
    zonas: Dict[str, List[float]]  # {'exito': [...], 'seguridad': [...], 'alerta': [...], 'brote': [...]}
    casos_actuales: List[int]
    tipo_ira: str


class CapacidadHospitalariaResponse(BaseModel):
    """Respuesta de capacidad hospitalaria"""
    hospitales: List[str]
    dotacion: Dict[str, int]  # Por hospital
    ocupacion_ira: Dict[str, int]  # Por hospital
    porcentaje_ocupacion: Dict[str, float]  # Por hospital


class VirusRespiratoriosResponse(BaseModel):
    """Respuesta de virus respiratorios"""
    por_semana: List[Dict[str, Any]]
    por_edad: List[Dict[str, Any]]


class IntoxicacionCOResponse(BaseModel):
    """Respuesta de intoxicación por CO"""
    por_ugd: List[Dict[str, Any]]
    comparacion: Dict[str, Any]


class DiarreasResponse(BaseModel):
    """Respuesta de diarreas"""
    corredor: Dict[str, Any]
    agentes_etiologicos: List[Dict[str, Any]]


class SUHResponse(BaseModel):
    """Respuesta de SUH"""
    casos: List[Dict[str, Any]]
    historico: List[Dict[str, Any]]


# ============================================================================
# Schemas para el nuevo sistema de generación automática con snippets
# ============================================================================

class EventoSeleccionado(BaseModel):
    """Evento seleccionado para incluir en el boletín"""
    tipo_eno_id: int = Field(..., description="ID del tipo de evento")
    incluir_charts: bool = Field(True, description="Incluir charts del evento")
    snippets_custom: Optional[List[str]] = Field(None, description="Códigos de snippets custom adicionales")


class GenerateDraftRequest(BaseModel):
    """Request para generar borrador de boletín automático"""
    semana: int = Field(..., description="Semana epidemiológica", ge=1, le=53)
    anio: int = Field(..., description="Año epidemiológico")
    num_semanas: int = Field(4, description="Número de semanas de análisis", ge=1, le=52)
    eventos_seleccionados: List[EventoSeleccionado] = Field(..., description="Eventos a incluir en el boletín")
    titulo_custom: Optional[str] = Field(None, description="Título personalizado (opcional)")


class BoletinMetadata(BaseModel):
    """Metadatos del boletín generado"""
    periodo_analisis: Dict[str, Any] = Field(..., description="Información del período analizado")
    eventos_incluidos: List[Dict[str, Any]] = Field(..., description="Eventos incluidos con sus datos")
    fecha_generacion: datetime = Field(..., description="Fecha de generación del borrador")


class GenerateDraftResponse(BaseModel):
    """Response al generar borrador de boletín"""
    boletin_instance_id: int = Field(..., description="ID de la instancia de boletín creada")
    content: str = Field(..., description="Contenido HTML generado (TipTap compatible)")
    metadata: BoletinMetadata = Field(..., description="Metadatos del boletín")

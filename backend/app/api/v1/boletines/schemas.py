"""
Schemas Pydantic para el sistema de boletines
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ============================================================================
# Schemas de Portada
# ============================================================================


class CoverConfig(BaseModel):
    """Configuración de la portada"""

    enabled: bool = Field(True, description="Mostrar portada")
    title: str = Field(..., description="Título del boletín")
    subtitle: Optional[str] = Field(None, description="Subtítulo")
    logo: Optional[str] = Field(None, description="URL o path al logo")
    background_image: Optional[str] = Field(None, description="Imagen de fondo")
    footer: Optional[str] = Field(None, description="Texto del pie de página")


# ============================================================================
# Schemas de Templates
# ============================================================================


class BoletinTemplateCreate(BaseModel):
    """Schema para crear template"""

    name: str = Field(
        ..., min_length=1, max_length=255, description="Nombre del template"
    )
    description: Optional[str] = Field(None, description="Descripción")
    category: str = Field(
        ..., description="Categoría: semanal, brote, tendencias, etc."
    )
    cover: Optional[CoverConfig] = Field(None, description="Configuración de portada")
    content: Optional[str] = Field(
        None, description="Contenido HTML del boletín (Tiptap)"
    )
    is_public: bool = Field(False, description="Template público")


class BoletinTemplateUpdate(BaseModel):
    """Schema para actualizar template"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    cover: Optional[CoverConfig] = None
    content: Optional[str] = None
    is_public: Optional[bool] = None


class BoletinTemplateResponse(BaseModel):
    """Schema de respuesta de template"""

    id: int
    name: str
    description: Optional[str]
    category: str
    cover: Optional[Dict[str, Any]]
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
    name: str = Field(
        ..., min_length=1, max_length=255, description="Nombre del boletín"
    )
    parameters: Dict[str, Any] = Field(..., description="Parámetros específicos")


class BoletinInstanceResponse(BaseModel):
    """Schema de respuesta de instancia"""

    id: int
    template_id: Optional[int]
    name: str
    parameters: Dict[str, Any]
    content: Optional[str]
    pdf_path: Optional[str]
    pdf_size: Optional[int]
    error_message: Optional[str]
    generated_by: Optional[int]
    generated_at: Optional[datetime]
    created_at: datetime

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
    zonas: Dict[
        str, List[float]
    ]  # {'exito': [...], 'seguridad': [...], 'alerta': [...], 'brote': [...]}
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


class CasoEpidemiologicoSeleccionado(BaseModel):
    """CasoEpidemiologico seleccionado para incluir en el boletín"""

    tipo_eno_id: int = Field(..., description="ID del tipo de evento")
    incluir_charts: bool = Field(True, description="Incluir charts del evento")
    snippets_custom: Optional[List[str]] = Field(
        None, description="Códigos de snippets custom adicionales"
    )


class GenerateDraftRequest(BaseModel):
    """Request para generar borrador de boletín automático"""

    semana: int = Field(..., description="Semana epidemiológica", ge=1, le=53)
    anio: int = Field(..., description="Año epidemiológico")
    num_semanas: int = Field(
        4, description="Número de semanas de análisis", ge=1, le=52
    )
    eventos_seleccionados: List[CasoEpidemiologicoSeleccionado] = Field(
        ..., description="CasoEpidemiologicos a incluir en el boletín"
    )
    titulo_custom: Optional[str] = Field(
        None, description="Título personalizado (opcional)"
    )


class BoletinMetadata(BaseModel):
    """Metadatos del boletín generado"""

    periodo_analisis: Dict[str, Any] = Field(
        ..., description="Información del período analizado"
    )
    eventos_incluidos: List[Dict[str, Any]] = Field(
        ..., description="CasoEpidemiologicos incluidos con sus datos"
    )
    fecha_generacion: datetime = Field(
        ..., description="Fecha de generación del borrador"
    )


class GenerateDraftResponse(BaseModel):
    """Response al generar borrador de boletín"""

    boletin_instance_id: int = Field(
        ..., description="ID de la instancia de boletín creada"
    )
    content: str = Field(..., description="Contenido HTML generado (TipTap compatible)")
    metadata: BoletinMetadata = Field(..., description="Metadatos del boletín")
    warnings: Optional[List[str]] = Field(
        None, description="Advertencias de validación"
    )


# ============================================================================
# Schemas para configuración de Template (BoletinTemplateConfig)
# ============================================================================


class BoletinTemplateConfigResponse(BaseModel):
    """Response de configuración de template de boletines"""

    id: int
    static_content_template: Dict[str, Any] = Field(
        ...,
        description="Template base en formato TipTap JSON (incluye selectedEventsPlaceholder)",
    )
    event_section_template: Dict[str, Any] = Field(
        default_factory=dict,
        description="Template de sección de evento (se repite por cada evento seleccionado)",
    )
    updated_at: Optional[datetime] = Field(None, description="Última actualización")
    updated_by: Optional[int] = Field(None, description="Usuario que actualizó")

    class Config:
        from_attributes = True


class UpdateStaticContentRequest(BaseModel):
    """Request para actualizar contenido estático"""

    content: Dict[str, Any] = Field(..., description="Contenido TipTap JSON")


class UpdateEventSectionTemplateRequest(BaseModel):
    """Request para actualizar template de sección de evento"""

    content: Dict[str, Any] = Field(
        ..., description="Template TipTap JSON de sección de evento"
    )

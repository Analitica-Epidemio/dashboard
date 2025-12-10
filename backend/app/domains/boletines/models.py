"""
Modelos de base de datos para el sistema de boletines epidemiológicos
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Column, Index, Text
from sqlalchemy.orm import Mapped
from sqlmodel import Field, Relationship

from app.core.models import BaseModel
from app.domains.boletines.constants import TipoBloque, TipoVisualizacion


class BoletinSnippet(BaseModel, table=True):
    """
    Snippet reutilizable para boletines epidemiologicos.

    Un snippet es un fragmento de template HTML con placeholders Jinja2
    que puede ser renderizado con diferentes variables.

    Categorias tipicas:
    - estructura: portada, introduccion, conclusion, footer
    - evento: templates para diferentes tipos de eventos
    """

    __tablename__ = "boletin_snippets"

    codigo: str = Field(
        max_length=100,
        index=True,
        unique=True,
        description="Codigo unico del snippet (ej: portada, introduccion)",
    )
    nombre: str = Field(max_length=255, description="Nombre descriptivo del snippet")
    descripcion: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Descripcion del proposito del snippet",
    )
    categoria: str = Field(
        max_length=50,
        index=True,
        description="Categoria del snippet (estructura, evento, etc.)",
    )
    template: str = Field(
        sa_column=Column(Text, nullable=False),
        description="Template HTML con placeholders Jinja2",
    )
    variables_schema: Dict[str, Any] = Field(
        sa_column=Column(JSON, nullable=False),
        description="Schema de variables requeridas por el template",
    )
    condiciones: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Condiciones para aplicar este snippet",
    )
    orden: int = Field(default=0, description="Orden de renderizado del snippet")
    is_active: bool = Field(default=True, description="Si el snippet esta activo")


class BoletinTemplateConfig(BaseModel, table=True):
    """
    Configuración única del template de boletín (singleton).
    Solo existe UN registro en esta tabla (id=1).

    Arquitectura:
    - static_content_template: Contenido base del boletín (portada, autoridades, metodología)
      Incluye un bloque placeholder "selectedEventsPlaceholder" donde se insertan los eventos
    - event_section_template: Template TipTap que se repite para CADA evento seleccionado
      Usa variables como {{ tipo_evento }}, {{ semana }}, etc.
    """

    __tablename__ = "boletin_template_config"

    # Contenido TipTap base con estructura fija
    # Incluye bloque "selectedEventsPlaceholder" donde se insertan eventos dinámicos
    static_content_template: Dict[str, Any] = Field(
        sa_column=Column(JSON, nullable=False),
        description="TipTap JSON del contenido base (portada, intro, autoridades, metodología)",
    )

    # Template de sección de evento - se repite para cada evento seleccionado
    # Variables: {{ tipo_evento }}, {{ semana }}, {{ anio }}, {{ num_semanas }}, etc.
    event_section_template: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
        description="TipTap JSON del template de sección de evento (se repite por cada evento)",
    )

    updated_by: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
        description="Usuario que actualizó la configuración",
    )


class CapacidadHospitalaria(BaseModel, table=True):
    """
    Capacidad de camas hospitalarias por UGD y semana epidemiológica.
    Reemplaza datos ficticios hardcodeados.
    """

    __tablename__ = "capacidad_hospitalaria"

    ugd: str = Field(
        max_length=100, index=True, description="Unidad de Gestión Descentralizada"
    )
    semana_epidemiologica: int = Field(index=True, description="Semana epidemiológica")
    anio: int = Field(index=True, description="Año")

    camas_totales: int = Field(description="Total de camas disponibles")
    camas_ocupadas: int = Field(description="Camas ocupadas")
    porcentaje_ocupacion: float = Field(description="Porcentaje de ocupación (0-100)")

    fecha_registro: date = Field(description="Fecha de registro de los datos")


class VirusRespiratorio(BaseModel, table=True):
    """
    Detección de virus respiratorios por semana epidemiológica.
    Reemplaza datos ficticios hardcodeados.
    """

    __tablename__ = "virus_respiratorio"

    semana_epidemiologica: int = Field(index=True, description="Semana epidemiológica")
    anio: int = Field(index=True, description="Año")
    virus_tipo: str = Field(
        max_length=100, description="Tipo de virus (Influenza A, VSR, etc.)"
    )

    casos_positivos: int = Field(description="Casos positivos detectados")
    casos_testeados: int = Field(description="Total de casos testeados")
    porcentaje_positividad: float = Field(
        description="Porcentaje de positividad (0-100)"
    )

    fecha_registro: date = Field(description="Fecha de registro de los datos")


class BoletinTemplate(BaseModel, table=True):
    """
    Plantilla reutilizable para boletines epidemiológicos.
    SIMPLIFICADA: Solo contiene metadatos y contenido HTML generado con TipTap.
    """

    __tablename__ = "boletin_templates"

    name: str = Field(max_length=255, index=True, description="Nombre de la plantilla")
    description: Optional[str] = Field(
        default=None, sa_column=Column(Text), description="Descripción de la plantilla"
    )
    category: str = Field(
        max_length=50,
        index=True,
        description="Categoría (semanal, brote, tendencias, etc.)",
    )

    # Configuración de portada (JSON)
    # { "enabled": true, "title": "...", "subtitle": "...", "footer": "..." }
    cover: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON), description="Configuración de portada"
    )

    # Contenido HTML del boletín (Tiptap)
    content: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Contenido HTML del boletín editado con Tiptap",
    )

    # Permisos y visibilidad
    is_public: bool = Field(
        default=True, description="Si es visible para todos los usuarios"
    )
    is_system: bool = Field(
        default=False, description="Si es una plantilla del sistema (no editable)"
    )
    created_by: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
        description="Usuario que creó la plantilla",
    )

    # Relaciones
    instances: Mapped[List["BoletinInstance"]] = Relationship(back_populates="template")


class BoletinInstance(BaseModel, table=True):
    """
    Instancia específica de un boletín generado.
    Contiene los parámetros usados y referencia al PDF generado.
    """

    __tablename__ = "boletin_instances"

    name: str = Field(
        max_length=255, index=True, description="Nombre del boletín generado"
    )
    template_id: Optional[int] = Field(
        default=None,
        foreign_key="boletin_templates.id",
        index=True,
        description="ID de la plantilla usada (None para boletines generados automáticamente)",
    )

    # Parámetros usados para generar el boletín (JSON)
    # { "periodo": "2024-W40", "departamento": "Rawson", "filtros_aplicados": {...} }
    parameters: Dict[str, Any] = Field(
        sa_column=Column(JSON, nullable=False), description="Parámetros de generación"
    )

    # Snapshot de la configuración del template al momento de generar (JSON)
    # Guarda widgets y layout para que cambios futuros no afecten el historial
    template_snapshot: Dict[str, Any] = Field(
        sa_column=Column(JSON, nullable=False), description="Snapshot del template"
    )

    # Contenido HTML editable (TipTap)
    content: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Contenido HTML del boletín (editable con TipTap)",
    )

    # Archivo PDF generado
    pdf_path: Optional[str] = Field(
        default=None, max_length=500, description="Path al archivo PDF generado"
    )
    pdf_size: Optional[int] = Field(default=None, description="Tamaño del PDF en bytes")

    # Metadatos de generación
    generated_at: Optional[datetime] = Field(
        default=None, description="Fecha de generación exitosa"
    )
    error_message: Optional[str] = Field(
        default=None, sa_column=Column(Text), description="Mensaje de error si falló"
    )

    # Usuario que generó el boletín
    generated_by: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
        description="Usuario que generó el boletín",
    )

    # Relaciones
    template: Mapped[Optional[BoletinTemplate]] = Relationship(
        back_populates="instances"
    )


# =============================================================================
# Modelos de Secciones y Bloques Configurables
# =============================================================================


class BoletinSeccion(BaseModel, table=True):
    """
    Sección temática del boletín epidemiológico.

    Agrupa bloques relacionados bajo un tema común (IRA, Diarreas, SUH, etc.).
    """

    __tablename__ = "boletin_secciones"
    __table_args__ = (
        Index("idx_boletin_seccion_slug", "slug"),
        Index("idx_boletin_seccion_orden", "orden"),
        Index("idx_boletin_seccion_activo", "activo"),
    )

    slug: str = Field(
        max_length=100,
        unique=True,
        index=True,
        description="Identificador único kebab-case",
    )
    titulo: str = Field(
        max_length=300,
        description="Título de la sección",
    )
    contenido_intro: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Contenido TipTap JSON introductorio opcional",
    )
    orden: int = Field(default=0, index=True)
    activo: bool = Field(default=True, index=True)
    descripcion: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
    )

    bloques: List["BoletinBloque"] = Relationship(
        back_populates="seccion",
        sa_relationship_kwargs={"lazy": "selectin", "order_by": "BoletinBloque.orden"},
    )


class BoletinBloque(BaseModel, table=True):
    """
    Bloque individual de visualización/datos del boletín.

    Configura qué métrica consultar, cómo agrupar, qué cálculos aplicar
    y de dónde obtener las series (catálogos dinámicos o config manual).
    """

    __tablename__ = "boletin_bloques"
    __table_args__ = (
        Index("idx_boletin_bloque_slug", "slug"),
        Index("idx_boletin_bloque_seccion", "seccion_id"),
        Index("idx_boletin_bloque_orden", "orden"),
        Index("idx_boletin_bloque_activo", "activo"),
    )

    seccion_id: int = Field(
        foreign_key="boletin_secciones.id",
        index=True,
    )
    slug: str = Field(
        max_length=100,
        unique=True,
        index=True,
    )
    titulo_template: str = Field(
        max_length=500,
        description="Template Jinja2 para título",
    )

    # Configuración de query
    tipo_bloque: TipoBloque = Field()
    tipo_visualizacion: TipoVisualizacion = Field()
    metrica_codigo: str = Field(max_length=100)
    dimensiones: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    compute: Optional[str] = Field(default=None, max_length=100)

    # Criterios y series
    criterios_fijos: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
    )
    series_source: Optional[str] = Field(default=None, max_length=200)
    series_config: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        sa_column=Column(JSON),
    )

    # Visual y estado
    config_visual: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
    )
    orden: int = Field(default=0, index=True)
    activo: bool = Field(default=True, index=True)
    descripcion: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
    )

    seccion: Optional[BoletinSeccion] = Relationship(back_populates="bloques")

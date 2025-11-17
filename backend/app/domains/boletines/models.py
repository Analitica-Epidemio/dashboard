"""
Modelos de base de datos para el sistema de boletines epidemiológicos
"""

from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, Relationship

from app.core.models import BaseModel


class BoletinTemplate(BaseModel, table=True):
    """
    Plantilla reutilizable para boletines epidemiológicos.
    Contiene la estructura (layout, widgets, filtros) pero no los datos específicos.
    """
    __tablename__ = "boletin_templates"

    name: str = Field(max_length=255, index=True, description="Nombre de la plantilla")
    description: Optional[str] = Field(default=None, sa_column=Column(Text), description="Descripción de la plantilla")
    category: str = Field(max_length=50, index=True, description="Categoría (semanal, brote, tendencias, etc.)")
    thumbnail: Optional[str] = Field(default=None, max_length=500, description="URL o path a imagen de preview")

    # Configuración del layout (JSON)
    # { "type": "grid", "columns": 12, "rowHeight": 40, "margin": [10, 10] }
    layout: Dict[str, Any] = Field(sa_column=Column(JSON, nullable=False), description="Configuración del layout")

    # Widgets del boletín (JSON Array)
    # [{ "id": "widget-1", "type": "kpi", "position": {...}, "data_config": {...}, "visual_config": {...} }]
    widgets: List[Dict[str, Any]] = Field(sa_column=Column(JSON, nullable=False), description="Widgets del boletín")

    # Configuración de portada (JSON)
    # { "enabled": true, "title": "...", "subtitle": "...", "footer": "..." }
    cover: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON), description="Configuración de portada")

    # Filtros globales (JSON)
    # { "temporal": {...}, "geografico": {...}, "demografico": {...} }
    global_filters: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON), description="Filtros globales")

    # Contenido HTML del boletín (Tiptap)
    content: Optional[str] = Field(default=None, sa_column=Column(Text), description="Contenido HTML del boletín editado con Tiptap")

    # Permisos y visibilidad
    is_public: bool = Field(default=True, description="Si es visible para todos los usuarios")
    is_system: bool = Field(default=False, description="Si es una plantilla del sistema (no editable)")
    created_by: Optional[int] = Field(default=None, foreign_key="users.id", description="Usuario que creó la plantilla")

    # Relaciones
    instances: List["BoletinInstance"] = Relationship(back_populates="template")


class BoletinInstance(BaseModel, table=True):
    """
    Instancia específica de un boletín generado.
    Contiene los parámetros usados y referencia al PDF generado.
    """
    __tablename__ = "boletin_instances"

    name: str = Field(max_length=255, index=True, description="Nombre del boletín generado")
    template_id: int = Field(foreign_key="boletin_templates.id", index=True, description="ID de la plantilla usada")

    # Parámetros usados para generar el boletín (JSON)
    # { "periodo": "2024-W40", "departamento": "Rawson", "filtros_aplicados": {...} }
    parameters: Dict[str, Any] = Field(sa_column=Column(JSON, nullable=False), description="Parámetros de generación")

    # Snapshot de la configuración del template al momento de generar (JSON)
    # Guarda widgets y layout para que cambios futuros no afecten el historial
    template_snapshot: Dict[str, Any] = Field(sa_column=Column(JSON, nullable=False), description="Snapshot del template")

    # Estado de generación
    status: str = Field(
        default="pending",
        max_length=20,
        index=True,
        description="Estado: pending, generating, completed, failed"
    )

    # Archivo PDF generado
    pdf_path: Optional[str] = Field(default=None, max_length=500, description="Path al archivo PDF generado")
    pdf_size: Optional[int] = Field(default=None, description="Tamaño del PDF en bytes")

    # Metadatos de generación
    generated_at: Optional[datetime] = Field(default=None, description="Fecha de generación exitosa")
    error_message: Optional[str] = Field(default=None, sa_column=Column(Text), description="Mensaje de error si falló")

    # Usuario que generó el boletín
    generated_by: Optional[int] = Field(default=None, foreign_key="users.id", description="Usuario que generó el boletín")

    # Relaciones
    template: Optional[BoletinTemplate] = Relationship(back_populates="instances")


class QueryDefinition(BaseModel, table=True):
    """
    Catálogo de queries disponibles para usar en widgets.
    Permite reutilizar queries entre diferentes templates.
    """
    __tablename__ = "boletin_queries"

    name: str = Field(max_length=255, unique=True, index=True, description="Nombre identificador de la query")
    description: Optional[str] = Field(default=None, sa_column=Column(Text), description="Descripción de la query")
    category: str = Field(max_length=50, index=True, description="Categoría (enos, ira, capacidad, etc.)")

    # Endpoint o SQL query (JSON)
    # { "type": "endpoint", "url": "/api/analytics/top-enos", "method": "GET" }
    # o { "type": "sql", "query": "SELECT ...", "params": [...] }
    query_config: Dict[str, Any] = Field(sa_column=Column(JSON, nullable=False), description="Configuración de la query")

    # Parámetros requeridos (JSON Array)
    # [{ "name": "fecha_inicio", "type": "date", "required": true }]
    required_params: List[Dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
        description="Parámetros requeridos"
    )

    # Esquema del resultado esperado (JSON)
    # { "type": "array", "items": { "type": "object", "properties": {...} } }
    result_schema: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON), description="Esquema del resultado")

    # Ejemplo de respuesta (JSON)
    example_response: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON), description="Ejemplo de respuesta")

    is_active: bool = Field(default=True, description="Si la query está activa")

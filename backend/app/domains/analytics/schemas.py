"""
Schemas para Analytics - grupos de eventos y configuraciones para visualizaciones.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GrupoEvento(BaseModel):
    """Modelo para grupos de eventos epidemiológicos."""

    id: int = Field(..., description="ID único del grupo")
    nombre: str = Field(..., description="Nombre del grupo de eventos")
    tipo: str = Field(..., description="Tipo: 'simple' o 'grupo'")
    descripcion: Optional[str] = Field(None, description="Descripción del grupo")
    activo: bool = Field(True, description="Si está activo para visualización")

    # Configuración
    clasificaciones_disponibles: List[str] = Field(
        ..., description="Clasificaciones disponibles para el grupo"
    )
    graficos_especiales: List[str] = Field(
        default_factory=list, description="Gráficos especiales del grupo"
    )

    # Metadata
    orden: int = Field(default=100, description="Orden para mostrar en UI")


class EventoDentroGrupo(BaseModel):
    """Evento específico dentro de un grupo."""

    id: int = Field(..., description="ID único del evento")
    tipo_eno_id: int = Field(..., description="ID del tipo ENO")
    nombre: str = Field(..., description="Nombre del evento específico")
    grupo_id: int = Field(..., description="ID del grupo al que pertenece")
    grupo_nombre: str = Field(..., description="Nombre del grupo")

    # Configuraciones específicas
    clasificaciones: Optional[List[str]] = Field(
        None, description="Clasificaciones específicas (null = usar del grupo)"
    )
    estrategia: Optional[str] = Field(
        None, description="Estrategia específica del evento"
    )

    # Stats
    total_casos: int = Field(0, description="Total de casos de este evento")
    casos_confirmados: int = Field(0, description="Casos confirmados")
    casos_sospechosos: int = Field(0, description="Casos sospechosos")
    ultimo_caso: Optional[str] = Field(None, description="Fecha del último caso")


class ConfiguracionVisualizacion(BaseModel):
    """Configuración para tipos de visualización disponibles."""

    id: str = Field(..., description="ID del tipo de gráfico")
    nombre: str = Field(..., description="Nombre descriptivo")
    descripcion: Optional[str] = Field(None, description="Descripción del gráfico")
    tipo: str = Field(..., description="Tipo: bar, line, pie, area, table, etc")
    parametros: Dict[str, Any] = Field(
        default_factory=dict, description="Parámetros específicos del gráfico"
    )
    requiere_parametros: List[str] = Field(
        default_factory=list, description="Parámetros requeridos"
    )

    # Disponibilidad
    disponible_para_grupos: List[str] = Field(
        default_factory=list, description="Grupos que pueden usar este gráfico"
    )
    disponible_para_todos: bool = Field(
        True, description="Si está disponible para todos los grupos"
    )


# Response models para la API
class GrupoEventoResponse(BaseModel):
    """Respuesta para un grupo de eventos."""

    grupo: GrupoEvento
    eventos: List[EventoDentroGrupo]
    graficos_disponibles: List[ConfiguracionVisualizacion]


class ListaGruposResponse(BaseModel):
    """Respuesta para la lista de grupos."""

    grupos: List[GrupoEvento]
    total: int


class DatosVisualizacionRequest(BaseModel):
    """Request para obtener datos de visualización."""

    grupo_id: int = Field(..., description="ID del grupo")
    evento_ids: List[int] = Field(
        default_factory=list,
        description="IDs específicos de eventos (vacío = todos del grupo)",
    )
    clasificacion: str = Field("todos", description="Clasificación a filtrar")
    fecha_desde: Optional[str] = Field(None, description="Fecha desde (YYYY-MM-DD)")
    fecha_hasta: Optional[str] = Field(None, description="Fecha hasta (YYYY-MM-DD)")
    tipo_grafico: str = Field(..., description="Tipo de gráfico solicitado")
    parametros_extra: Dict[str, Any] = Field(
        default_factory=dict, description="Parámetros adicionales"
    )


class DatosVisualizacionResponse(BaseModel):
    """Respuesta con datos para visualización."""

    grupo: str = Field(..., description="Nombre del grupo")
    eventos: List[str] = Field(..., description="Nombres de eventos incluidos")
    clasificacion: str = Field(..., description="Clasificación filtrada")
    tipo_grafico: str = Field(..., description="Tipo de gráfico")

    # Datos del gráfico
    datos: List[Dict[str, Any]] = Field(..., description="Datos del gráfico")
    metadatos: Dict[str, Any] = Field(
        default_factory=dict, description="Metadatos adicionales"
    )

    # Info contextual
    total_casos: int = Field(..., description="Total de casos en el resultado")
    fecha_generacion: str = Field(..., description="Timestamp de generación")
    filtros_aplicados: Dict[str, Any] = Field(
        ..., description="Resumen de filtros aplicados"
    )

"""
Modelo de Agrupaciones de Agentes Etiológicos.

Las agrupaciones permiten agrupar múltiples agentes individuales bajo una
etiqueta visual para gráficos del boletín y dashboard.

Ejemplo:
    Agrupación "Influenza A" agrupa:
    - Virus Influenza A por IF o Test rápido
    - Virus Influenza A por PCR NO estudiados por IF ni Test rápido
    - Virus Influenza A por PCR negativos por IF o Test rápido

Esto permite que en los gráficos se muestre una sola serie "Flu A"
que suma todas las variantes.
"""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, Index, Text
from sqlmodel import Field, Relationship, SQLModel

from app.core.models import BaseModel

if TYPE_CHECKING:
    from .models import AgenteEtiologico


class AgrupacionAgenteLink(SQLModel, table=True):
    """
    Tabla de enlace many-to-many entre AgrupacionAgentes y AgenteEtiologico.

    Nota: Usa SQLModel directamente (no BaseModel) para evitar el id
    auto-increment que conflictúa con la primary key compuesta.
    """

    __tablename__ = "agrupacion_agente_link"
    __table_args__ = (
        Index("idx_agrupacion_link_agrupacion", "agrupacion_id"),
        Index("idx_agrupacion_link_agente", "agente_id"),
    )

    agrupacion_id: int = Field(
        foreign_key="agrupacion_agentes.id",
        primary_key=True,
        description="ID de la agrupación",
    )
    agente_id: int = Field(
        foreign_key="agente_etiologico.id",
        primary_key=True,
        description="ID del agente etiológico",
    )


class AgrupacionAgentes(BaseModel, table=True):
    """
    Agrupación visual de agentes etiológicos para charts.

    Permite agrupar múltiples agentes individuales bajo una etiqueta
    para visualización en gráficos del boletín y dashboard.

    Ejemplos:
        - "Influenza A" agrupa 3 variantes de Flu A
        - "VSR" contiene solo Virus Sincicial Respiratorio
        - "Salmonella" agrupa S. enteritidis, S. typhimurium, S. spp., etc.

    Atributos:
        slug: Identificador único (ej: "influenza-a")
        nombre: Nombre completo (ej: "Influenza A")
        nombre_corto: Para gráficos (ej: "Flu A")
        color: Color hex para charts (ej: "#F44336")
        categoria: Grupo funcional (respiratorio, enterico, etc.)
    """

    __tablename__ = "agrupacion_agentes"
    __table_args__ = (
        Index("idx_agrupacion_slug", "slug"),
        Index("idx_agrupacion_categoria", "categoria"),
        Index("idx_agrupacion_activo", "activo"),
    )

    # Identificación
    slug: str = Field(
        max_length=100,
        unique=True,
        index=True,
        description="Identificador único kebab-case (ej: 'influenza-a', 'vsr')",
    )
    nombre: str = Field(
        max_length=200,
        description="Nombre completo de la agrupación (ej: 'Influenza A')",
    )
    nombre_corto: str = Field(
        max_length=50,
        description="Nombre corto para gráficos y tablas (ej: 'Flu A')",
    )

    # Visualización
    color: str = Field(
        max_length=20,
        default="#6B7280",
        description="Color hex para gráficos (ej: '#F44336')",
    )

    # Clasificación
    categoria: str = Field(
        max_length=50,
        index=True,
        description="Categoría funcional: respiratorio, enterico, vectorial, etc.",
    )

    # Ordenamiento
    orden: int = Field(
        default=0,
        description="Orden de aparición en UI (menor = primero)",
    )

    # Metadata
    descripcion: Optional[str] = Field(
        None,
        sa_column=Column(Text),
        description="Descripción de la agrupación y qué incluye",
    )

    # Estado
    activo: bool = Field(
        default=True,
        index=True,
        description="Si la agrupación está activa para uso en el sistema",
    )

    # Relación many-to-many con AgenteEtiologico
    agentes: List["AgenteEtiologico"] = Relationship(
        back_populates="agrupaciones",
        link_model=AgrupacionAgenteLink,
    )

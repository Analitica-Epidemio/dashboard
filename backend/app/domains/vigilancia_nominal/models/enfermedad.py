"""
Enfermedades de Notificación Obligatoria (ENO) y sus agrupaciones.

Este módulo define el catálogo de enfermedades que por normativa del
Ministerio de Salud de Argentina deben notificarse al SNVS cuando se detectan.

IMPORTANTE: Este catálogo solo aplica a vigilancia NOMINAL (casos individuales).
Para vigilancia agregada (conteos semanales) ver vigilancia_agregada/models/catalogos.py

Modelos:
--------
- Enfermedad: Una enfermedad de notificación obligatoria (Dengue, Rabia, SUH, etc.)
- GrupoDeEnfermedades: Agrupación para reportes (Arbovirosis, Zoonosis, etc.)
- EnfermedadGrupo: Tabla de unión N:M (una enfermedad puede estar en varios grupos)

Ejemplos de enfermedades:
- Dengue, Zika, Chikungunya (arbovirosis)
- Rabia humana
- Síndrome Urémico Hemolítico (SUH)
- Chagas, Tuberculosis
- Sarampión, Rubéola
"""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import CheckConstraint, Index, SmallInteger, UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlmodel import Field, Relationship, SQLModel

from app.core.models import BaseModel

if TYPE_CHECKING:
    from app.domains.vigilancia_nominal.models.caso import (
        CasoEpidemiologico,
        CasoGrupoEnfermedad,
    )


class EnfermedadGrupo(SQLModel, table=True):
    """
    Relación muchos-a-muchos entre Enfermedad y GrupoDeEnfermedades.

    Tabla de unión pura - solo contiene las FKs como primary key compuesta.
    No tiene id autoincrement, created_at, ni updated_at (best practice para M2M).

    Permite que una enfermedad pertenezca a múltiples grupos simultáneamente.

    Ejemplo:
        Neumonía puede pertenecer tanto al grupo "IRA" como a "Invasivas".
        Dengue pertenece a "Arbovirosis" y también podría estar en "Vectoriales".
    """

    __tablename__ = "enfermedad_grupo"
    __table_args__ = (
        UniqueConstraint("id_enfermedad", "id_grupo", name="uq_enfermedad_grupo"),
    )

    id_enfermedad: int = Field(
        foreign_key="enfermedad.id",
        primary_key=True,
        description="ID de la enfermedad",
    )
    id_grupo: int = Field(
        foreign_key="grupo_de_enfermedades.id",
        primary_key=True,
        description="ID del grupo",
    )

    # Relaciones
    enfermedad: Mapped["Enfermedad"] = Relationship(back_populates="enfermedad_grupos")
    grupo: Mapped["GrupoDeEnfermedades"] = Relationship(
        back_populates="enfermedad_grupos"
    )


class GrupoDeEnfermedades(BaseModel, table=True):
    """
    Agrupación de enfermedades para reportes y visualización.

    Los grupos permiten:
    - Agrupar enfermedades relacionadas para dashboards
    - Definir ventanas temporales para mapas de calor
    - Generar boletines epidemiológicos consolidados

    Ejemplos:
        - "Arbovirosis": Dengue, Zika, Chikungunya, Fiebre Amarilla
        - "Inmunoprevenibles": Sarampión, Rubéola, Parotiditis
        - "Zoonosis": Rabia, Leptospirosis, Hantavirus
        - "ETS": Sífilis, Gonorrea, VIH

    Atributos:
        nombre: Nombre del grupo (ej: "Arbovirosis")
        slug: Identificador único kebab-case para URLs y templates (ej: "arbovirosis")
        ventana_dias_visualizacion: Días a mostrar en mapas (None = acumulado anual)
    """

    __tablename__ = "grupo_de_enfermedades"
    __table_args__ = (Index("ix_grupo_enfermedades_slug", "slug"),)

    nombre: str = Field(
        ...,
        max_length=150,
        description="Nombre del grupo (ej: 'Arbovirosis', 'Zoonosis')",
    )
    slug: Optional[str] = Field(
        None,
        max_length=100,
        unique=True,
        index=True,
        description="Identificador único kebab-case para URLs y templates (ej: 'arbovirosis')",
    )
    descripcion: Optional[str] = Field(
        None,
        max_length=500,
        description="Descripción del grupo y qué enfermedades incluye",
    )
    ventana_dias_visualizacion: Optional[int] = Field(
        None,
        ge=1,
        le=365,
        sa_type=SmallInteger,
        description="Ventana temporal en días para mapas de calor. None = acumulado anual.",
    )

    # Relaciones
    enfermedad_grupos: Mapped[List["EnfermedadGrupo"]] = Relationship(
        back_populates="grupo"
    )
    casos_en_grupo: Mapped[List["CasoGrupoEnfermedad"]] = Relationship(
        back_populates="grupo"
    )

    @property
    def usa_acumulado_anual(self) -> bool:
        """True si este grupo muestra datos acumulados del año en vez de ventana temporal."""
        return self.ventana_dias_visualizacion is None


class Enfermedad(BaseModel, table=True):
    """
    Enfermedad de Notificación Obligatoria (ENO).

    Representa una enfermedad que por normativa del Ministerio de Salud
    debe ser reportada al sistema de vigilancia epidemiológica cuando se detecta.

    IMPORTANTE: Solo aplica a vigilancia NOMINAL (casos individuales).
    Para datos agregados (CLI_P26, LAB_P26) ver TipoCasoEpidemiologicoPasivo.

    Ejemplos:
        - Dengue: slug "dengue", incubación 4-10 días
        - Rabia humana: slug "rabia-humana", incubación 20-90 días
        - SUH: slug "sindrome-uremico-hemolitico"

    Atributos:
        nombre: Nombre oficial (ej: "Dengue")
        slug: Identificador único kebab-case para URLs y templates (ej: "dengue")
        id_snvs: ID en el Sistema Nacional de Vigilancia de la Salud
        periodo_incubacion_min_dias: Período de incubación mínimo
        periodo_incubacion_max_dias: Período de incubación máximo
    """

    __tablename__ = "enfermedad"
    __table_args__ = (
        Index("ix_enfermedad_slug", "slug", unique=True),
        CheckConstraint(
            "periodo_incubacion_max_dias IS NULL OR "
            "periodo_incubacion_min_dias IS NULL OR "
            "periodo_incubacion_max_dias >= periodo_incubacion_min_dias",
            name="ck_enfermedad_incubacion_valida",
        ),
    )

    # Identificación
    nombre: str = Field(
        ...,
        max_length=200,
        description="Nombre oficial de la enfermedad (ej: 'Dengue', 'Rabia humana')",
    )
    slug: Optional[str] = Field(
        None,
        max_length=100,
        unique=True,
        index=True,
        description="Identificador único kebab-case para URLs y templates (ej: 'dengue')",
    )

    # Integración con SNVS
    id_snvs: Optional[int] = Field(
        None,
        unique=True,
        index=True,
        description="ID de la enfermedad en el Sistema Nacional de Vigilancia de la Salud",
    )

    descripcion: Optional[str] = Field(
        None,
        max_length=500,
        description="Descripción clínica y epidemiológica de la enfermedad",
    )

    # Período de incubación (útil para análisis de brotes)
    periodo_incubacion_min_dias: Optional[int] = Field(
        None,
        ge=0,
        le=365,
        sa_type=SmallInteger,
        description="Período de incubación mínimo en días (ej: 4 para Dengue)",
    )
    periodo_incubacion_max_dias: Optional[int] = Field(
        None,
        ge=0,
        le=365,
        sa_type=SmallInteger,
        description="Período de incubación máximo en días (ej: 10 para Dengue)",
    )

    fuente_referencia: Optional[str] = Field(
        None,
        max_length=500,
        description="URL de fuente oficial (OMS, CDC, Ministerio de Salud)",
    )

    # Relaciones
    enfermedad_grupos: Mapped[List["EnfermedadGrupo"]] = Relationship(
        back_populates="enfermedad"
    )
    casos: Mapped[List["CasoEpidemiologico"]] = Relationship(
        back_populates="enfermedad"
    )

    @property
    def periodo_incubacion_promedio_dias(self) -> Optional[float]:
        """Calcula el promedio del período de incubación en días."""
        if self.periodo_incubacion_min_dias and self.periodo_incubacion_max_dias:
            return (
                self.periodo_incubacion_min_dias + self.periodo_incubacion_max_dias
            ) / 2
        return None

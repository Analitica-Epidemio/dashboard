"""
Catálogo de Agentes Etiológicos (patógenos).

Los agentes etiológicos son patógenos (virus, bacterias, parásitos) que causan
enfermedades y pueden detectarse en:

1. Vigilancia nominal: casos individuales (ej: paciente X tiene VSR)
2. Vigilancia agregada: conteos de laboratorio (ej: 50 muestras positivas para Rotavirus)

Ejemplos de agentes:
- Virus: VSR, Influenza A/B, SARS-CoV-2, Rotavirus, Adenovirus
- Bacterias: Salmonella, Shigella, STEC, Streptococcus pneumoniae
- Parásitos: Giardia, Cryptosporidium, Toxoplasma
"""

from typing import Optional

from sqlalchemy import Column, Index, Text
from sqlmodel import Field

from app.core.models import BaseModel


class CategoriaAgente:
    """Categorías de agentes etiológicos."""
    VIRUS = "virus"
    BACTERIA = "bacteria"
    PARASITO = "parasito"
    HONGO = "hongo"
    PRION = "prion"
    OTRO = "otro"


class GrupoAgente:
    """Grupos funcionales de agentes (para filtrado en gráficos)."""
    RESPIRATORIO = "respiratorio"
    ENTERICO = "enterico"
    VECTORIAL = "vectorial"
    ZOONOTICO = "zoonotico"
    TRANSMISION_SEXUAL = "transmision_sexual"
    SANGUINEO = "sanguineo"
    OTRO = "otro"


class AgenteEtiologico(BaseModel, table=True):
    """
    Catálogo de agentes etiológicos (patógenos).

    Representa virus, bacterias, parásitos y otros agentes causantes
    de enfermedades que se detectan en el laboratorio.

    Este catálogo es COMPARTIDO entre vigilancia nominal y agregada.

    Ejemplos:
        - VSR (Virus Sincicial Respiratorio): slug "vsr", grupo "respiratorio"
        - Influenza A: slug "influenza-a", grupo "respiratorio"
        - Rotavirus: slug "rotavirus", grupo "enterico"
        - Salmonella spp.: slug "salmonella", grupo "enterico"

    Atributos:
        slug: Identificador único kebab-case para URLs y templates (ej: "vsr")
        nombre: Nombre completo (ej: "Virus Sincicial Respiratorio")
        nombre_corto: Nombre corto para gráficos (ej: "VSR")
        categoria: Tipo de patógeno (virus, bacteria, parasito, etc.)
        grupo: Grupo funcional (respiratorio, enterico, vectorial, etc.)
    """

    __tablename__ = "agente_etiologico"
    __table_args__ = (
        Index("idx_agente_slug", "slug"),
        Index("idx_agente_categoria", "categoria"),
        Index("idx_agente_grupo", "grupo"),
        Index("idx_agente_activo", "activo"),
    )

    # Identificación
    slug: str = Field(
        max_length=100,
        unique=True,
        index=True,
        description="Identificador único kebab-case para URLs y templates (ej: 'vsr', 'rotavirus')"
    )
    nombre: str = Field(
        max_length=200,
        description="Nombre completo del agente (ej: 'Virus Sincicial Respiratorio')"
    )
    nombre_corto: str = Field(
        max_length=50,
        description="Nombre corto para gráficos y tablas (ej: 'VSR', 'Flu A')"
    )

    # Integración con SNVS
    id_snvs: Optional[int] = Field(
        None,
        index=True,
        description="ID del agente en el Sistema Nacional de Vigilancia de la Salud"
    )

    # Clasificación
    categoria: str = Field(
        max_length=50,
        index=True,
        description="Categoría del patógeno: virus, bacteria, parasito, hongo, prion, otro"
    )
    grupo: str = Field(
        max_length=50,
        index=True,
        description="Grupo funcional: respiratorio, enterico, vectorial, zoonotico, etc."
    )

    # Metadata
    descripcion: Optional[str] = Field(
        None,
        sa_column=Column(Text),
        description="Descripción del agente y su relevancia epidemiológica"
    )

    # Estado
    activo: bool = Field(
        default=True,
        index=True,
        description="Si el agente está activo para uso en el sistema"
    )

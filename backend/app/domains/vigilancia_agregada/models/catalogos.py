"""
Catálogos para vigilancia pasiva (agregada).

Contiene los catálogos específicos del SNVS para datos de vigilancia pasiva:
- TipoCasoEpidemiologicoPasivo: Catálogo de eventos (ETI, Neumonía, etc.) - análogo a Enfermedad
- RangoEtario: Grupos de edad del SNVS
"""

from typing import TYPE_CHECKING, List, Optional

from pydantic import field_validator
from sqlalchemy import Index, SmallInteger
from sqlmodel import Field, Relationship

from app.core.models import BaseModel
from app.domains.vigilancia_agregada.constants import OrigenDatosPasivos

if TYPE_CHECKING:
    from app.domains.vigilancia_agregada.models.conteos import (
        ConteoCamasIRA,
        ConteoCasosClinicos,
        ConteoEstudiosLab,  # Solo para RangoEtario (que aun tiene rango etario)
    )


class TipoCasoEpidemiologicoPasivo(BaseModel, table=True):
    """
    Catálogo de eventos de vigilancia pasiva (CLI_P26 y CLI_P26_INT).

    Contiene eventos CLINICOS y de INTERNACION.
    NO incluye datos de laboratorio (LAB_P26) - esos usan AgenteEtiologico.

    Ejemplos por origen:
    - CLINICO: ETI, Neumonía, Bronquiolitis, Diarreas, Varicela
    - INTERNACION: Pacientes en ARM por IRA, Pacientes en UTI por IRA

    Los datos de LABORATORIO (VSR, Rotavirus, etc.) usan el catalogo
    compartido AgenteEtiologico de app.domains.catalogos.agentes.

    Attributes:
        id_snvs: ID único del evento en el sistema SNVS
        nombre: Nombre descriptivo del evento
        grupo_nombre: Nombre del grupo al que pertenece (opcional)
        origen: De qué archivo/reporte proviene (CLI/INT)
    """

    __tablename__ = "tipo_evento_pasivo"
    __table_args__ = (
        Index("ix_tipo_evento_pasivo_snvs", "id_snvs"),
        Index("ix_tipo_evento_pasivo_origen", "origen"),
    )

    # ═══════════════════════════════════════════════════════════════
    # Identificación SNVS
    # ═══════════════════════════════════════════════════════════════

    id_snvs: int = Field(
        ...,
        index=True,
        description="ID del evento en SNVS (ID_SNVS_EVENTO_AGRP)",
    )

    # ═══════════════════════════════════════════════════════════════
    # Datos descriptivos
    # ═══════════════════════════════════════════════════════════════

    nombre: str = Field(
        ...,
        min_length=1,
        max_length=300,
        description="Nombre del evento (NOMBREEVENTOAGRP)",
    )

    grupo_nombre: Optional[str] = Field(
        None,
        max_length=300,
        description="Nombre del grupo de eventos (NOMBREGRPEVENTOAGRP)",
    )

    grupo_id_snvs: Optional[int] = Field(
        None,
        description="ID del grupo en SNVS (IDEVENTOAGRUPADO)",
    )

    # ═══════════════════════════════════════════════════════════════
    # Clasificación
    # ═══════════════════════════════════════════════════════════════

    origen: OrigenDatosPasivos = Field(
        ...,
        description="Origen de datos: clinico (CLI_P26), laboratorio (LAB_P26), internacion (CLI_P26_INT)",
    )

    # ═══════════════════════════════════════════════════════════════
    # Metadata adicional
    # ═══════════════════════════════════════════════════════════════

    descripcion: Optional[str] = Field(
        None,
        max_length=500,
        description="Descripción adicional del evento",
    )

    activo: bool = Field(
        default=True,
        description="Si el evento está activo para nuevas cargas",
    )

    # ═══════════════════════════════════════════════════════════════
    # Relaciones
    # ═══════════════════════════════════════════════════════════════

    conteos_clinicos: List["ConteoCasosClinicos"] = Relationship(
        back_populates="tipo_evento"
    )
    # NOTA: conteos_laboratorio ahora usa AgenteEtiologico del catalogo compartido
    conteos_internacion: List["ConteoCamasIRA"] = Relationship(
        back_populates="tipo_evento"
    )


class RangoEtario(BaseModel, table=True):
    """
    Catálogo de rangos etarios (grupos de edad) del SNVS.

    Los rangos de edad en vigilancia pasiva son predefinidos por el SNVS
    y varían según el origen de datos:

    - CLINICO: 15+ grupos detallados (0-6m, 6-11m, 1a, 2-4a, 5-9a, etc.)
    - INTERNACION: 5 grupos simplificados (Adultos <60, >=60, Pediát <3, etc.)

    Attributes:
        id_snvs: ID del grupo de edad en SNVS
        nombre: Descripción del rango (ej: "de 25 a 34 años")
        edad_desde: Edad mínima en años (inclusive)
        edad_hasta: Edad máxima en años (inclusive, None = sin límite)
    """

    __tablename__ = "rango_etario"
    __table_args__ = (
        Index("ix_rango_etario_snvs", "id_snvs"),
    )

    # ═══════════════════════════════════════════════════════════════
    # Identificación SNVS
    # ═══════════════════════════════════════════════════════════════

    id_snvs: int = Field(
        ...,
        index=True,
        description="ID del grupo de edad en SNVS (IDEDAD)",
    )

    # ═══════════════════════════════════════════════════════════════
    # Datos descriptivos
    # ═══════════════════════════════════════════════════════════════

    nombre: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre del rango (ej: 'de 25 a 34 años', 'menores de 6 meses')",
    )

    # ═══════════════════════════════════════════════════════════════
    # Rango numérico (para cálculos y ordenamiento)
    # ═══════════════════════════════════════════════════════════════

    edad_desde: Optional[int] = Field(
        None,
        ge=0,
        le=150,
        sa_type=SmallInteger,
        description="Edad mínima del rango en años (inclusive). 0 = desde nacimiento",
    )

    edad_hasta: Optional[int] = Field(
        None,
        ge=0,
        le=150,
        sa_type=SmallInteger,
        description="Edad máxima del rango en años (inclusive). None = sin límite superior",
    )

    orden: int = Field(
        default=0,
        sa_type=SmallInteger,
        description="Orden para mostrar en UI (menor = primero)",
    )

    # ═══════════════════════════════════════════════════════════════
    # Clasificación
    # ═══════════════════════════════════════════════════════════════

    origen: OrigenDatosPasivos = Field(
        ...,
        description="Origen donde se usa este rango (clínico tiene más granularidad)",
    )

    # ═══════════════════════════════════════════════════════════════
    # Validators
    # ═══════════════════════════════════════════════════════════════

    @field_validator("edad_hasta")
    @classmethod
    def edad_hasta_mayor_que_desde(cls, v: Optional[int], info) -> Optional[int]:
        """Valida que edad_hasta >= edad_desde si ambos están definidos."""
        edad_desde = info.data.get("edad_desde")
        if v is not None and edad_desde is not None and v < edad_desde:
            raise ValueError(f"edad_hasta ({v}) debe ser >= edad_desde ({edad_desde})")
        return v

    # ═══════════════════════════════════════════════════════════════
    # Relaciones
    # ═══════════════════════════════════════════════════════════════

    conteos_clinicos: List["ConteoCasosClinicos"] = Relationship(
        back_populates="rango_etario"
    )
    conteos_laboratorio: List["ConteoEstudiosLab"] = Relationship(
        back_populates="rango_etario"
    )
    conteos_internacion: List["ConteoCamasIRA"] = Relationship(
        back_populates="rango_etario"
    )

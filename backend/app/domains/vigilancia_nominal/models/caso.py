"""
Casos epidemiológicos de vigilancia nominal.

CasoEpidemiologico es el modelo central de vigilancia nominal.
Representa un caso individual de una Enfermedad de Notificación Obligatoria.
"""

from datetime import date
from typing import TYPE_CHECKING, Dict, List, Optional

from sqlalchemy import JSON, BigInteger, Column, Index, Text, UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlmodel import Field, Relationship

from app.core.models import BaseModel
from app.domains.vigilancia_nominal.clasificacion.models import TipoClasificacion

if TYPE_CHECKING:
    from app.domains.territorio.establecimientos_models import Establecimiento
    from app.domains.territorio.geografia_models import Domicilio
    from app.domains.vigilancia_nominal.clasificacion.models import (
        EstrategiaClasificacion,
    )
    from app.domains.vigilancia_nominal.models.agentes import CasoAgente
    from app.domains.vigilancia_nominal.models.ambitos import AmbitosConcurrenciaCaso
    from app.domains.vigilancia_nominal.models.atencion import (
        ContactosNotificacion,
        DiagnosticoCasoEpidemiologico,
        InternacionCasoEpidemiologico,
        InvestigacionCasoEpidemiologico,
        TratamientoCasoEpidemiologico,
    )
    from app.domains.vigilancia_nominal.models.enfermedad import (
        Enfermedad,
        GrupoDeEnfermedades,
    )
    from app.domains.vigilancia_nominal.models.salud import (
        MuestraCasoEpidemiologico,
        Sintoma,
        VacunasCiudadano,
    )
    from app.domains.vigilancia_nominal.models.sujetos import Animal, Ciudadano


# =============================================================================
# TABLA DE UNIÓN: Caso <-> GrupoDeEnfermedades
# =============================================================================


class CasoGrupoEnfermedad(BaseModel, table=True):
    """
    Relación muchos-a-muchos entre CasoEpidemiologico y GrupoDeEnfermedades.

    Permite que un caso esté asociado a múltiples grupos de enfermedades.

    Ejemplo:
        Un caso de Neumonía puede estar en los grupos "IRA" e "Invasivas".
    """

    __tablename__ = "caso_grupo_enfermedad"
    __table_args__ = (
        UniqueConstraint("id_caso", "id_grupo", name="uq_caso_grupo_enfermedad"),
    )

    id_caso: int = Field(
        foreign_key="caso_epidemiologico.id",
        description="ID del caso epidemiológico",
    )
    id_grupo: int = Field(
        foreign_key="grupo_de_enfermedades.id",
        description="ID del grupo de enfermedades",
    )

    caso: Mapped["CasoEpidemiologico"] = Relationship(back_populates="caso_grupos")
    grupo: Mapped["GrupoDeEnfermedades"] = Relationship(back_populates="casos_en_grupo")


# =============================================================================
# ANTECEDENTE EPIDEMIOLÓGICO
# =============================================================================


class AntecedenteEpidemiologico(BaseModel, table=True):
    """
    Catálogo de antecedentes epidemiológicos (factores de riesgo).

    Ejemplos: Diabetes, Embarazo, Inmunodeprimido, Viaje reciente.
    """

    __tablename__ = "antecedente_epidemiologico"
    __table_args__ = (
        UniqueConstraint(
            "descripcion", name="uq_antecedente_epidemiologico_descripcion"
        ),
    )

    id_snvs_antecedente_epidemio: Optional[int] = Field(
        None, description="ID del antecedente en SNVS"
    )
    descripcion: Optional[str] = Field(
        None,
        max_length=150,
        description="Descripción del antecedente (ej: 'Diabetes', 'Embarazo')",
    )

    antecedentes_casos: Mapped[List["AntecedentesCasoEpidemiologico"]] = Relationship(
        back_populates="antecedente_epidemiologico_rel"
    )


# =============================================================================
# CASO EPIDEMIOLÓGICO
# =============================================================================


class CasoEpidemiologico(BaseModel, table=True):
    """
    Caso individual de vigilancia nominal.

    Representa un caso de una Enfermedad de Notificación Obligatoria (ENO)
    con datos del paciente, fechas, establecimiento de atención, etc.

    Es el modelo central del dominio de vigilancia nominal.

    Relaciones principales:
        - enfermedad: La ENO diagnosticada (Dengue, Rabia, etc.)
        - ciudadano: El paciente (si es humano)
        - animal: El sujeto (si es caso animal)
        - agentes_detectados: Patógenos encontrados (VSR, Rotavirus, etc.)
    """

    __tablename__ = "caso_epidemiologico"
    __table_args__ = (
        Index("idx_caso_fecha_minima", "fecha_minima_caso"),
        Index("idx_caso_domicilio_fecha", "id_domicilio", "fecha_minima_caso"),
        Index("idx_caso_enfermedad_fecha", "id_enfermedad", "fecha_minima_caso"),
    )

    # =========================================================================
    # Identificación
    # =========================================================================

    id_snvs: int = Field(
        sa_type=BigInteger,
        unique=True,
        index=True,
        description="ID único del caso en el Sistema Nacional de Vigilancia de la Salud",
    )

    # =========================================================================
    # Fechas epidemiológicas
    # =========================================================================

    fecha_minima_caso: Optional[date] = Field(
        None,
        description="Fecha más temprana del caso (mín de apertura, síntomas, consulta)",
    )
    fecha_minima_caso_semana_epi: int = Field(
        ..., index=True, description="Semana epidemiológica de fecha_minima_caso (1-53)"
    )
    fecha_minima_caso_anio_epi: int = Field(
        ..., index=True, description="Año epidemiológico de fecha_minima_caso"
    )
    fecha_inicio_sintomas: Optional[date] = Field(
        None, description="Fecha de inicio de síntomas"
    )
    es_caso_sintomatico: Optional[bool] = Field(
        None, description="True si el caso presenta síntomas"
    )
    fecha_apertura_caso: Optional[date] = Field(
        None, description="Fecha de apertura del caso en SNVS"
    )
    semana_epidemiologica_apertura: Optional[int] = Field(
        None, description="Semana epidemiológica de apertura"
    )
    anio_epidemiologico_apertura: Optional[int] = Field(
        None, description="Año epidemiológico de apertura"
    )
    fecha_nacimiento: Optional[date] = Field(
        None, description="Fecha de nacimiento del paciente"
    )
    fecha_primera_consulta: Optional[date] = Field(
        None, description="Fecha de primera consulta médica"
    )
    anio_epidemiologico_consulta: Optional[int] = Field(
        None, description="Año epidemiológico de consulta"
    )
    semana_epidemiologica_consulta: Optional[int] = Field(
        None, description="Semana epidemiológica de consulta"
    )
    semana_minima_calculada: Optional[int] = Field(
        None, description="Semana mínima calculada del caso"
    )
    anio_evento: Optional[int] = Field(None, description="Año calendario del evento")
    observaciones_texto: Optional[str] = Field(
        None,
        sa_column=Column(Text),
        description="Observaciones clínicas en texto libre",
    )
    fecha_consulta: Optional[date] = Field(None, description="Fecha de consulta")
    id_origen: Optional[str] = Field(
        None, max_length=200, description="Sistema de origen del registro"
    )
    semana_epidemiologica_sintomas: Optional[int] = Field(
        None, description="Semana epidemiológica de inicio de síntomas"
    )
    semana_epidemiologica_muestra: Optional[int] = Field(
        None, description="Semana epidemiológica de toma de muestra"
    )

    # =========================================================================
    # Foreign Keys
    # =========================================================================

    id_enfermedad: int = Field(
        foreign_key="enfermedad.id",
        description="ID de la Enfermedad de Notificación Obligatoria",
    )
    codigo_ciudadano: Optional[int] = Field(
        None,
        sa_type=BigInteger,
        foreign_key="ciudadano.codigo_ciudadano",
        description="Código del ciudadano (paciente humano)",
    )
    id_animal: Optional[int] = Field(
        None, foreign_key="animal.id", description="ID del animal (si es caso animal)"
    )
    id_establecimiento_consulta: Optional[int] = Field(
        None,
        foreign_key="establecimiento.id",
        description="Establecimiento donde se realizó la consulta",
    )
    id_establecimiento_notificacion: Optional[int] = Field(
        None,
        foreign_key="establecimiento.id",
        description="Establecimiento que notificó el caso",
    )
    id_establecimiento_carga: Optional[int] = Field(
        None,
        foreign_key="establecimiento.id",
        description="Establecimiento que cargó el registro",
    )
    id_domicilio: Optional[int] = Field(
        None,
        foreign_key="domicilio.id",
        index=True,
        description="Domicilio de residencia del paciente",
    )

    # =========================================================================
    # Clasificación
    # =========================================================================

    requiere_revision_especie: Optional[bool] = Field(
        False, description="True si requiere revisión de especie (animal)"
    )
    datos_originales_csv: Optional[Dict] = Field(
        None, sa_column=Column(JSON), description="Datos originales del CSV importado"
    )
    metadata_clasificacion: Optional[Dict] = Field(
        None,
        sa_column=Column(JSON),
        description="Metadata del proceso de clasificación",
    )
    clasificacion_manual: Optional[str] = Field(
        None, max_length=500, description="Clasificación original del SNVS"
    )
    clasificacion_estrategia: Optional[TipoClasificacion] = Field(
        None,
        max_length=255,
        description="Clasificación asignada por estrategia automática",
    )
    metadata_extraida: Optional[Dict] = Field(
        None, sa_column=Column(JSON), description="Metadata extraída del procesamiento"
    )
    confidence_score: Optional[float] = Field(
        None, description="Score de confianza de la clasificación (0.0 a 1.0)"
    )
    id_estrategia_aplicada: Optional[int] = Field(
        None,
        foreign_key="estrategia_clasificacion.id",
        description="ID de la estrategia de clasificación aplicada",
    )
    trazabilidad_clasificacion: Optional[Dict] = Field(
        None,
        sa_column=Column(JSON),
        description="Trazabilidad completa del proceso de clasificación",
    )

    # =========================================================================
    # Relaciones
    # =========================================================================

    enfermedad: Mapped["Enfermedad"] = Relationship(back_populates="casos")
    caso_grupos: Mapped[List["CasoGrupoEnfermedad"]] = Relationship(
        back_populates="caso"
    )
    ciudadano: Mapped[Optional["Ciudadano"]] = Relationship(back_populates="casos")
    animal: Mapped[Optional["Animal"]] = Relationship(back_populates="casos")
    estrategia_aplicada: Mapped[Optional["EstrategiaClasificacion"]] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[CasoEpidemiologico.id_estrategia_aplicada]"
        }
    )
    establecimiento_consulta: Mapped[Optional["Establecimiento"]] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[CasoEpidemiologico.id_establecimiento_consulta]"
        }
    )
    establecimiento_notificacion: Mapped[Optional["Establecimiento"]] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[CasoEpidemiologico.id_establecimiento_notificacion]"
        }
    )
    establecimiento_carga: Mapped[Optional["Establecimiento"]] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[CasoEpidemiologico.id_establecimiento_carga]"
        }
    )
    sintomas: Mapped[List["DetalleCasoSintomas"]] = Relationship(back_populates="caso")
    muestras: Mapped[List["MuestraCasoEpidemiologico"]] = Relationship(
        back_populates="caso"
    )
    antecedentes: Mapped[List["AntecedentesCasoEpidemiologico"]] = Relationship(
        back_populates="caso"
    )
    vacunas: Mapped[List["VacunasCiudadano"]] = Relationship(back_populates="caso")
    diagnosticos: Mapped[List["DiagnosticoCasoEpidemiologico"]] = Relationship(
        back_populates="caso"
    )
    internaciones: Mapped[List["InternacionCasoEpidemiologico"]] = Relationship(
        back_populates="caso"
    )
    tratamientos: Mapped[List["TratamientoCasoEpidemiologico"]] = Relationship(
        back_populates="caso"
    )
    investigaciones: Mapped[List["InvestigacionCasoEpidemiologico"]] = Relationship(
        back_populates="caso"
    )
    contactos: Mapped[List["ContactosNotificacion"]] = Relationship(
        back_populates="caso"
    )
    ambitos_concurrencia: Mapped[List["AmbitosConcurrenciaCaso"]] = Relationship(
        back_populates="caso"
    )
    domicilio: Mapped[Optional["Domicilio"]] = Relationship(back_populates="casos")
    agentes_detectados: Mapped[List["CasoAgente"]] = Relationship(
        back_populates="caso",
        sa_relationship_kwargs={"foreign_keys": "caso_agente.c.id_caso"},
    )


# =============================================================================
# DETALLE CASO SÍNTOMAS
# =============================================================================


class DetalleCasoSintomas(BaseModel, table=True):
    """
    Relación muchos-a-muchos entre CasoEpidemiologico y Sintoma.

    Registra qué síntomas presentó el paciente y cuándo aparecieron.
    """

    __tablename__ = "detalle_caso_sintomas"
    __table_args__ = (
        UniqueConstraint("id_caso", "id_sintoma", name="uq_caso_sintoma"),
    )

    semana_epidemiologica_aparicion_sintoma: Optional[int] = Field(
        None, description="Semana epidemiológica de aparición del síntoma"
    )
    fecha_inicio_sintoma: Optional[date] = Field(
        None, description="Fecha de inicio del síntoma"
    )
    anio_epidemiologico_sintoma: Optional[int] = Field(
        None, description="Año epidemiológico del síntoma"
    )

    id_caso: int = Field(
        foreign_key="caso_epidemiologico.id", description="ID del caso"
    )
    id_sintoma: int = Field(foreign_key="sintoma.id", description="ID del síntoma")

    caso: Mapped["CasoEpidemiologico"] = Relationship(back_populates="sintomas")
    sintoma: Mapped["Sintoma"] = Relationship(back_populates="detalle_casos")


# =============================================================================
# ANTECEDENTES DE UN CASO
# =============================================================================


class AntecedentesCasoEpidemiologico(BaseModel, table=True):
    """
    Relación muchos-a-muchos entre CasoEpidemiologico y AntecedenteEpidemiologico.

    Registra qué antecedentes/factores de riesgo tiene el paciente del caso.
    """

    __tablename__ = "antecedentes_caso_epidemiologico"
    __table_args__ = (
        UniqueConstraint(
            "id_caso", "id_antecedente_epidemiologico", name="uq_caso_antecedente"
        ),
    )

    fecha_antecedente_epidemiologico: Optional[date] = Field(
        None, description="Fecha del antecedente (si aplica)"
    )

    id_caso: int = Field(
        foreign_key="caso_epidemiologico.id", description="ID del caso"
    )
    id_antecedente_epidemiologico: int = Field(
        foreign_key="antecedente_epidemiologico.id", description="ID del antecedente"
    )

    caso: Mapped["CasoEpidemiologico"] = Relationship(back_populates="antecedentes")
    antecedente_epidemiologico_rel: Mapped["AntecedenteEpidemiologico"] = Relationship(
        back_populates="antecedentes_casos"
    )

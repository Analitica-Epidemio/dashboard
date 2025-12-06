"""
Sujetos epidemiológicos: Ciudadanos, Animales y Viajes.

Los sujetos son las entidades sobre las cuales se registran casos de vigilancia nominal.
- Ciudadano: Personas humanas con sus datos demográficos
- Animal: Animales involucrados en casos (ej: rabia, brucelosis)
- ViajesCiudadano: Viajes relevantes para rastreo epidemiológico

IMPORTANTE: Estos modelos solo aplican a vigilancia NOMINAL.
Los datos agregados no tienen sujetos individuales.
"""

from datetime import date
from typing import TYPE_CHECKING, Dict, List, Optional

from sqlalchemy import BigInteger, Column, JSON
from sqlmodel import Field, Relationship, UniqueConstraint

from app.core.models import BaseModel
from app.core.constants import SexoBiologico, TipoDocumento

if TYPE_CHECKING:
    from app.domains.vigilancia_nominal.models.caso import CasoEpidemiologico
    from app.domains.vigilancia_nominal.models.salud import Comorbilidad, VacunasCiudadano
    from app.domains.territorio.geografia_models import Domicilio, Localidad


# =============================================================================
# CIUDADANO
# =============================================================================


class Ciudadano(BaseModel, table=True):
    """
    Datos principales de ciudadanos (pacientes humanos).

    Es el sujeto más común en casos de vigilancia nominal.
    """

    __tablename__ = "ciudadano"
    __table_args__ = (
        UniqueConstraint("codigo_ciudadano", name="uk_ciudadano_codigo"),
        UniqueConstraint(
            "tipo_documento", "numero_documento", name="uk_ciudadano_documento"
        ),
        {"extend_existing": True},
    )

    # Código único del ciudadano (puede ser diferente del ID)
    codigo_ciudadano: int = Field(
        sa_type=BigInteger,
        unique=True,
        index=True,
        description="Código único del ciudadano",
    )

    # Identificación
    nombre: Optional[str] = Field(
        None, max_length=150, index=True, description="Nombre del ciudadano"
    )
    apellido: Optional[str] = Field(
        None, max_length=150, index=True, description="Apellido del ciudadano"
    )
    tipo_documento: Optional[TipoDocumento] = Field(
        None, index=True, description="Tipo de documento"
    )
    numero_documento: Optional[int] = Field(
        None, sa_type=BigInteger, index=True, description="Número de documento"
    )

    # Datos personales
    fecha_nacimiento: Optional[date] = Field(None, description="Fecha de nacimiento")
    sexo_biologico_al_nacer: Optional[SexoBiologico] = Field(
        None, description="Sexo biológico al nacer"
    )
    sexo_biologico: Optional[SexoBiologico] = Field(None, description="Sexo biológico")
    genero_autopercibido: Optional[str] = Field(
        None, max_length=150, description="Género autopercibido"
    )
    etnia: Optional[str] = Field(None, max_length=30, description="Etnia")

    # Relaciones
    domicilios: List["CiudadanoDomicilio"] = Relationship(back_populates="ciudadano")
    domicilios_historico: List["PersonaDomicilio"] = Relationship(back_populates="ciudadano")
    datos: List["CiudadanoDatos"] = Relationship(back_populates="ciudadano")
    casos: List["CasoEpidemiologico"] = Relationship(back_populates="ciudadano")
    comorbilidades: List["CiudadanoComorbilidades"] = Relationship(
        back_populates="ciudadano"
    )
    viajes: List["ViajesCiudadano"] = Relationship(back_populates="ciudadano")
    vacunas: List["VacunasCiudadano"] = Relationship(back_populates="ciudadano")


class CiudadanoDomicilio(BaseModel, table=True):
    """
    Domicilios de ciudadanos (vínculo con tabla normalizada Domicilio).

    Permite compartir el mismo domicilio entre múltiples ciudadanos
    y geocodificar una sola vez cada dirección única.
    """

    __tablename__ = "ciudadano_domicilio"

    # Foreign Keys
    codigo_ciudadano: int = Field(
        sa_type=BigInteger,
        foreign_key="ciudadano.codigo_ciudadano",
        description="Código del ciudadano",
    )
    id_domicilio: int = Field(
        foreign_key="domicilio.id",
        index=True,
        description="ID del domicilio normalizado",
    )

    # Relaciones
    ciudadano: "Ciudadano" = Relationship(back_populates="domicilios")
    domicilio: "Domicilio" = Relationship()


class CiudadanoDatos(BaseModel, table=True):
    """
    Datos adicionales de ciudadanos (histórico por evento).

    Guarda datos que pueden cambiar con el tiempo (ocupación, cobertura social).
    """

    __tablename__ = "ciudadano_datos"

    # Foreign Keys
    codigo_ciudadano: int = Field(
        sa_type=BigInteger,
        foreign_key="ciudadano.codigo_ciudadano",
        description="Código del ciudadano",
    )
    id_caso: int = Field(  # Cambiado de id_evento a id_caso para consistencia
        foreign_key="caso_epidemiologico.id",
        description="ID del caso asociado (para mantener historial temporal)",
    )

    # Campos propios
    cobertura_social_obra_social: Optional[str] = Field(
        None, max_length=250, description="Obra social o cobertura de salud"
    )
    edad_anos_actual: Optional[int] = Field(None, description="Edad actual en años")
    ocupacion_laboral: Optional[str] = Field(
        None, max_length=150, description="Ocupación laboral"
    )
    informacion_contacto: Optional[str] = Field(
        None,
        max_length=150,
        description="Información de contacto (teléfono, email, etc)",
    )
    es_declarado_pueblo_indigena: Optional[bool] = Field(
        None, description="Se declara perteneciente a pueblo indígena"
    )
    es_embarazada: Optional[bool] = Field(
        None,
        description="Indica si la ciudadana está embarazada",
    )

    # Relaciones
    ciudadano: "Ciudadano" = Relationship(back_populates="datos")


class CiudadanoComorbilidades(BaseModel, table=True):
    """Relación N:M entre Ciudadano y Comorbilidad."""

    __tablename__ = "ciudadano_comorbilidades"

    # Foreign Keys
    codigo_ciudadano: int = Field(
        sa_type=BigInteger,
        foreign_key="ciudadano.codigo_ciudadano",
        description="Código del ciudadano",
    )
    id_comorbilidad: int = Field(
        foreign_key="comorbilidad.id", description="ID de la comorbilidad"
    )

    # Relaciones
    ciudadano: "Ciudadano" = Relationship(back_populates="comorbilidades")
    comorbilidad: "Comorbilidad" = Relationship()


class PersonaDomicilio(BaseModel, table=True):
    """
    Historial temporal de domicilios de una persona.

    Mantiene el registro de CUÁNDO una persona vivió en DÓNDE.
    Permite queries como "¿Dónde vivía Juan en enero 2023?".
    """

    __tablename__ = "persona_domicilio"
    __table_args__ = (
        UniqueConstraint(
            "codigo_ciudadano",
            "id_domicilio",
            "fecha_desde",
            name="uq_persona_domicilio_fecha"
        ),
    )

    # Foreign Keys
    codigo_ciudadano: int = Field(
        sa_type=BigInteger,
        foreign_key="ciudadano.codigo_ciudadano",
        index=True,
        description="Código del ciudadano"
    )
    id_domicilio: int = Field(
        foreign_key="domicilio.id",
        index=True,
        description="ID del domicilio"
    )

    # Rango temporal
    fecha_desde: date = Field(
        ...,
        index=True,
        description="Fecha desde la cual vive en este domicilio"
    )
    fecha_hasta: Optional[date] = Field(
        None,
        description="Fecha hasta la cual vivió (NULL = domicilio actual)"
    )

    # Relaciones
    ciudadano: "Ciudadano" = Relationship(back_populates="domicilios_historico")
    domicilio: "Domicilio" = Relationship()


# =============================================================================
# ANIMAL
# =============================================================================


class Animal(BaseModel, table=True):
    """
    Datos de animales para casos epidemiológicos.

    Usado en enfermedades zoonóticas como rabia, brucelosis, etc.
    """

    __tablename__ = "animal"
    __table_args__ = {"extend_existing": True}

    # Campos propios
    especie: str = Field(..., max_length=100, description="Especie del animal")
    raza: Optional[str] = Field(None, max_length=100, description="Raza del animal")
    sexo: Optional[str] = Field(None, max_length=20, description="Sexo del animal")
    edad_aproximada: Optional[int] = Field(None, description="Edad aproximada en meses")
    identificacion: Optional[str] = Field(
        None,
        max_length=100,
        description="Identificación del animal (collar, chip, etc)",
    )

    # Clasificación taxonómica
    subespecie: Optional[str] = Field(
        None,
        max_length=100,
        description="Subespecie o nombre científico completo",
    )
    clasificacion_taxonomica: Optional[Dict] = Field(
        None,
        sa_column=Column(JSON),
        description="Información taxonómica estructurada",
    )
    origen_deteccion: Optional[str] = Field(
        None,
        max_length=255,
        description="Cómo se detectó: 'automatico', 'manual', 'revision'",
    )
    confidence_deteccion: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confianza en la detección automática (0.0 a 1.0)",
    )

    # Datos del propietario
    propietario_nombre: Optional[str] = Field(
        None, max_length=150, description="Nombre del propietario"
    )
    propietario_contacto: Optional[str] = Field(
        None, max_length=150, description="Contacto del propietario"
    )

    # Ubicación
    id_localidad_indec: Optional[int] = Field(
        None,
        sa_type=BigInteger,
        foreign_key="localidad.id_localidad_indec",
        description="ID de la localidad INDEC",
    )
    direccion: Optional[str] = Field(
        None, max_length=200, description="Dirección donde se encuentra el animal"
    )

    # Relaciones
    localidad: Optional["Localidad"] = Relationship()
    casos: List["CasoEpidemiologico"] = Relationship(back_populates="animal")


# =============================================================================
# VIAJES
# =============================================================================


class ViajesCiudadano(BaseModel, table=True):
    """
    Registro de viajes realizados por ciudadanos.

    Importante para rastreo epidemiológico de posibles exposiciones
    o transmisión de enfermedades entre regiones.
    """

    __tablename__ = "viajes_ciudadano"
    __table_args__ = {"extend_existing": True}

    # ID SNVS como identificador único
    id_snvs_viaje_epidemiologico: int = Field(
        unique=True, index=True, description="ID SNVS del viaje epidemiológico"
    )

    # Foreign Keys
    codigo_ciudadano: int = Field(
        sa_type=BigInteger,
        foreign_key="ciudadano.codigo_ciudadano",
        description="Código del ciudadano",
    )
    id_localidad_destino_viaje: Optional[int] = Field(
        None,
        sa_type=BigInteger,
        foreign_key="localidad.id_localidad_indec",
        description="ID de la localidad de destino del viaje",
    )

    # Campos propios
    fecha_inicio_viaje: Optional[date] = Field(
        None, description="Fecha de inicio del viaje"
    )
    fecha_finalizacion_viaje: Optional[date] = Field(
        None, description="Fecha de finalización del viaje"
    )

    # Relaciones
    ciudadano: "Ciudadano" = Relationship(back_populates="viajes")
    localidad: Optional["Localidad"] = Relationship()

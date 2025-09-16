"""Modelos del dominio de Ciudadanos."""

from datetime import date
from typing import TYPE_CHECKING, Dict, List, Optional

from sqlalchemy import JSON, BigInteger, Column
from sqlmodel import Field, Relationship, UniqueConstraint

from app.core.models import BaseModel
from app.core.shared.enums import FrecuenciaOcurrencia, SexoBiologico, TipoDocumento

if TYPE_CHECKING:
    from app.domains.eventos.models import Evento
    from app.domains.localidades.models import Localidad
    from app.domains.salud.models import Comorbilidad, VacunasCiudadano


class Ciudadano(BaseModel, table=True):
    """Datos principales de ciudadanos"""

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
    )  # si esta vacio, poner sexo
    sexo_biologico: Optional[SexoBiologico] = Field(None, description="Sexo biológico")
    genero_autopercibido: Optional[str] = Field(
        None, max_length=150, description="Género autopercibido"
    )
    etnia: Optional[str] = Field(None, max_length=30, description="Etnia")

    # Relaciones
    domicilios: List["CiudadanoDomicilio"] = Relationship(back_populates="ciudadano")
    datos: List["CiudadanoDatos"] = Relationship(back_populates="ciudadano")
    eventos: List["Evento"] = Relationship(back_populates="ciudadano")
    comorbilidades: List["CiudadanoComorbilidades"] = Relationship(
        back_populates="ciudadano"
    )
    viajes: List["ViajesCiudadano"] = Relationship(back_populates="ciudadano")
    vacunas: List["VacunasCiudadano"] = Relationship(back_populates="ciudadano")


class Animal(BaseModel, table=True):
    """Datos principales de animales para eventos epidemiológicos"""

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

    # Campos adicionales para mejor clasificación
    subespecie: Optional[str] = Field(
        None,
        max_length=100,
        description="Subespecie o nombre científico completo (ej: TADARIDA BRASILIENSIS)",
    )
    clasificacion_taxonomica: Optional[Dict] = Field(
        None,
        sa_column=Column(JSON),
        description="Información taxonómica estructurada extraída automáticamente",
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

    # Datos del propietario/responsable
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
    eventos: List["Evento"] = Relationship(back_populates="animal")


class CiudadanoDomicilio(BaseModel, table=True):
    """Domicilios de ciudadanos"""

    __tablename__ = "ciudadano_domicilio"

    # Foreign Keys
    codigo_ciudadano: int = Field(
        sa_type=BigInteger,
        foreign_key="ciudadano.codigo_ciudadano",
        description="Código del ciudadano",
    )
    id_localidad_indec: int = Field(
        sa_type=BigInteger,
        foreign_key="localidad.id_localidad_indec",
        description="ID de la localidad INDEC",
    )

    # Campos propios
    calle_domicilio: Optional[str] = Field(
        None, max_length=150, description="Calle del domicilio"
    )
    numero_domicilio: Optional[str] = Field(
        None, max_length=10, description="Número del domicilio"
    )
    barrio_popular: Optional[str] = Field(
        None, max_length=150, description="Nombre del barrio"
    )

    # Relaciones
    ciudadano: "Ciudadano" = Relationship(back_populates="domicilios")
    localidad: "Localidad" = Relationship()


class CiudadanoDatos(BaseModel, table=True):
    """Datos adicionales de ciudadanos (histórico)"""

    __tablename__ = "ciudadano_datos"

    # Foreign Keys
    codigo_ciudadano: int = Field(
        sa_type=BigInteger,
        foreign_key="ciudadano.codigo_ciudadano",
        description="Código del ciudadano",
    )
    id_evento: int = Field(
        foreign_key="evento.id",
        description="ID del evento asociado (para mantener historial temporal)",
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

    # Agregado por Ignacio - Campos faltantes del CSV epidemiológico
    es_embarazada: Optional[bool] = Field(
        None,
        description="Indica si la ciudadana está embarazada (relevante para análisis de riesgo epidemiológico)",
    )

    # Relaciones
    ciudadano: "Ciudadano" = Relationship(back_populates="datos")


class CiudadanoComorbilidades(BaseModel, table=True):
    """Comorbilidades de ciudadanos"""

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


class ViajesCiudadano(BaseModel, table=True):
    """
    Registro de viajes realizados por ciudadanos.

    Importante para rastreo epidemiológico de posibles exposiciones
    o transmisión de enfermedades entre regiones.
    """

    __tablename__ = "viajes_ciudadano"
    __table_args__ = {"extend_existing": True}

    # Usar ID SNVS como identificador único
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


class AmbitosConcurrenciaEvento(BaseModel, table=True):
    """Ámbitos de concurrencia durante eventos epidemiológicos"""

    __tablename__ = "ambitos_concurrencia_evento"

    # Foreign Keys
    id_evento: int = Field(foreign_key="evento.id", description="ID del evento")
    id_localidad_ambito_ocurrencia: Optional[int] = Field(
        None,
        sa_type=BigInteger,
        foreign_key="localidad.id_localidad_indec",
        description="ID de la localidad INDEC",
    )

    # Campos propios
    nombre_lugar_ocurrencia: Optional[str] = Field(
        None, max_length=150, description="Nombre del lugar"
    )
    tipo_lugar_ocurrencia: Optional[str] = Field(
        None, max_length=150, description="Tipo de lugar"
    )
    localidad_ambito_ocurrencia: Optional[str] = Field(
        None, max_length=150, description="Localidad del ámbito"
    )
    fecha_ambito_ocurrencia: Optional[date] = Field(
        None, description="Fecha de ocurrencia"
    )
    frecuencia_concurrencia: Optional[FrecuenciaOcurrencia] = Field(
        None, description="Frecuencia de concurrencia al lugar"
    )
    es_sitio_probable_adquisicion_infeccion: Optional[bool] = Field(
        None, description="Es el sitio probable donde se adquirió la infección"
    )
    es_sitio_probable_diseminacion_infeccion: Optional[bool] = Field(
        None, description="Es el sitio probable donde se diseminó la infección"
    )

    # Relaciones
    evento: "Evento" = Relationship(back_populates="ambitos_concurrencia")
    localidad: Optional["Localidad"] = Relationship()

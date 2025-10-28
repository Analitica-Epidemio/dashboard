"""Modelos del dominio de Ciudadanos."""

from datetime import date
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger
from sqlmodel import Field, Relationship, UniqueConstraint

from app.core.models import BaseModel
from app.core.shared.enums import SexoBiologico, TipoDocumento

if TYPE_CHECKING:
    from app.domains.eventos_epidemiologicos.eventos.models import Evento
    from app.domains.territorio.geografia_models import Localidad, Domicilio
    from app.domains.atencion_medica.salud_models import Comorbilidad, VacunasCiudadano
    from .viajes_models import ViajesCiudadano


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
    domicilios_historico: List["PersonaDomicilio"] = Relationship(back_populates="ciudadano")
    datos: List["CiudadanoDatos"] = Relationship(back_populates="ciudadano")
    eventos: List["Evento"] = Relationship(back_populates="ciudadano")
    comorbilidades: List["CiudadanoComorbilidades"] = Relationship(
        back_populates="ciudadano"
    )
    viajes: List["ViajesCiudadano"] = Relationship(back_populates="ciudadano")
    vacunas: List["VacunasCiudadano"] = Relationship(back_populates="ciudadano")


class CiudadanoDomicilio(BaseModel, table=True):
    """
    Domicilios de ciudadanos (vínculo con tabla normalizada Domicilio).

    Esta tabla vincula ciudadanos con domicilios normalizados, permitiendo:
    - Compartir el mismo domicilio entre múltiples ciudadanos
    - Geocodificar una sola vez cada dirección única
    - Análisis de clusters (múltiples personas en la misma dirección)
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


class PersonaDomicilio(BaseModel, table=True):
    """
    Historial temporal de domicilios de una persona.

    Tabla intermedia que mantiene el registro de CUÁNDO una persona vivió en DÓNDE.
    - Permite saber dónde vivía la persona en cualquier momento del tiempo
    - Múltiples personas pueden vivir en el mismo domicilio
    - Una persona puede tener múltiples domicilios a lo largo del tiempo

    Casos de uso:
    - "¿Dónde vivía Juan en enero 2023?" → Query por rango de fechas
    - "¿Quiénes viven actualmente en San Martin 123?" → Query por fecha_hasta IS NULL
    - "Mudanzas de María" → ORDER BY fecha_desde
    """

    __tablename__ = "persona_domicilio"
    __table_args__ = (
        # Un ciudadano no puede tener dos domicilios simultáneos con mismas fechas
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
        description="Fecha hasta la cual vivió en este domicilio (NULL = domicilio actual)"
    )

    # Relaciones
    ciudadano: "Ciudadano" = Relationship(back_populates="domicilios_historico")
    domicilio: "Domicilio" = Relationship()
from datetime import date
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, Text
from sqlmodel import Field, Relationship

from app.core.models import BaseModel

if TYPE_CHECKING:
    from app.domains.ciudadanos.models import Ciudadano
    from app.domains.diagnosticos.models import (
        DiagnosticoEvento,
        EstudioEvento,
        InternacionEvento,
        TratamientoEvento,
    )
    from app.domains.establecimientos.models import EstablecimientoEvento
    from app.domains.investigaciones.models import (
        ContactosNotificacion,
        InvestigacionEvento,
    )
    from app.domains.salud.models import MuestraEvento, Sintoma, VacunasCiudadano


class Evento(BaseModel, table=True):
    """Eventos epidemiológicos"""

    __tablename__ = "evento"

    # Campos propios
    nombre: str = Field(..., description="Nombre del evento epidemiológico")
    # TODO: Deberíamos de tener un grupo evento tabla???
    grupo_evento: Optional[str] = Field(
        None, max_length=150, description="Grupo al que pertenece el evento"
    )

    # Relaciones
    ciudadanos_eventos: List["CiudadanoEvento"] = Relationship(back_populates="evento")


class AntecedenteEpidemiologico(BaseModel, table=True):
    """Antecedentes epidemiológicos"""

    __tablename__ = "antecedente_epidemiologico"

    # Campos propios
    id_snvs_antecedente_epidemio: Optional[int] = Field(
        None, description="ID SNVS del antecedente epidemiológico"
    )
    descripcion: Optional[str] = Field(
        None, max_length=150, description="Descripción del antecedente"
    )

    # Relaciones
    antecedentes_eventos: List["AntecedentesEpidemiologicosEvento"] = Relationship(
        back_populates="antecedente_epidemiologico_rel"
    )


class CiudadanoEvento(BaseModel, table=True):
    """Eventos de ciudadanos"""

    __tablename__ = "ciudadano_evento"

    # Campos propios
    id_evento_caso: int = Field(
        sa_type=BigInteger,
        unique=True,
        index=True,
        description="ID único del evento caso epidemiológico",
    )
    fecha_minima_evento: date = Field(
        ..., description="Fecha mínima registrada del evento"
    )
    fecha_inicio_sintomas: Optional[date] = Field(
        None, description="Fecha de inicio de síntomas"
    )
    es_caso_sintomatico: Optional[bool] = Field(
        None, description="Indica si el caso presenta síntomas"
    )
    fecha_apertura_caso: Optional[date] = Field(
        None, description="Fecha de apertura del caso en el sistema"
    )
    semana_epidemiologica_apertura: Optional[int] = Field(
        None, description="Semana epidemiológica de apertura del caso"
    )
    anio_epidemiologico_apertura: Optional[int] = Field(
        None, description="Año epidemiológico de apertura del caso"
    )
    edad_anos_al_momento_apertura: Optional[int] = Field(
        None, description="Edad en años al momento de apertura del caso"
    )
    fecha_primera_consulta: Optional[date] = Field(
        None, description="Fecha de la primera consulta médica"
    )
    # TODO: En el modelo original había comentarios para parsear " " (espacios) como blank/null
    anio_epidemiologico_consulta: Optional[int] = Field(
        None, description="Año epidemiológico de la consulta"
    )
    semana_epidemiologica_consulta: Optional[int] = Field(
        None, description="Semana epidemiológica de la consulta"
    )
    semana_minima_calculada: Optional[int] = Field(
        None,
        description="Semana mínima calculada del evento (calculado por epi Chubut)",
    )
    anio_evento: Optional[int] = Field(
        None, description="Año calendario del evento (calculado por epi Chubut)"
    )
    # TODO: El modelo original indicaba que observaciones es un seteo de varias observaciones de distintas tablas
    observaciones_texto: Optional[str] = Field(
        None, sa_column=Text, description="Observaciones en texto libre sobre el evento"
    )
    
    # Agregado por Ignacio - Campos faltantes del CSV epidemiológico
    fecha_consulta: Optional[date] = Field(
        None, description="Fecha de primera consulta médica del caso (usar NULL cuando sea desconocida)"
    )
    id_origen: Optional[str] = Field(
        None, max_length=200, description="ID del sistema origen (SNVS, otro sistema, usar 'Desconocido' si no se especifica)"
    )
    semana_epidemiologica_sintomas: Optional[int] = Field(
        None, description="Semana epidemiológica específica de inicio de síntomas"
    )
    semana_epidemiologica_muestra: Optional[int] = Field(
        None, description="Semana epidemiológica específica de toma de muestra"
    )

    # Foreign Keys
    id_evento: int = Field(foreign_key="evento.id", description="ID del evento")
    codigo_ciudadano: int = Field(
        sa_type=BigInteger,
        foreign_key="ciudadano.codigo_ciudadano",
        description="Código del ciudadano",
    )

    # Relaciones
    evento: "Evento" = Relationship(back_populates="ciudadanos_eventos")
    ciudadano: "Ciudadano" = Relationship(back_populates="eventos")
    sintomas: List["DetalleEventoSintomas"] = Relationship(
        back_populates="ciudadano_evento"
    )
    muestras: List["MuestraEvento"] = Relationship(back_populates="ciudadano_evento")
    antecedentes: List["AntecedentesEpidemiologicosEvento"] = Relationship(
        back_populates="ciudadano_evento"
    )
    vacunas: List["VacunasCiudadano"] = Relationship(back_populates="ciudadano_evento")
    establecimientos: List["EstablecimientoEvento"] = Relationship(
        back_populates="ciudadano_evento"
    )
    diagnosticos: List["DiagnosticoEvento"] = Relationship(
        back_populates="ciudadano_evento"
    )
    internaciones: List["InternacionEvento"] = Relationship(
        back_populates="ciudadano_evento"
    )
    estudios: List["EstudioEvento"] = Relationship(back_populates="ciudadano_evento")
    tratamientos: List["TratamientoEvento"] = Relationship(
        back_populates="ciudadano_evento"
    )
    investigaciones: List["InvestigacionEvento"] = Relationship(
        back_populates="ciudadano_evento"
    )
    contactos: List["ContactosNotificacion"] = Relationship(
        back_populates="ciudadano_evento"
    )


class DetalleEventoSintomas(BaseModel, table=True):
    """
    Detalle de síntomas específicos presentados durante un evento epidemiológico.

    Permite registrar múltiples síntomas por evento con sus fechas correspondientes.
    """

    __tablename__ = "detalle_evento_sintomas"

    # Campos propios
    semana_epidemiologica_aparicion_sintoma: Optional[int] = Field(
        None, description="Semana epidemiológica cuando apareció el síntoma"
    )
    fecha_inicio_sintoma: Optional[date] = Field(
        None, description="Fecha de inicio del síntoma específico"
    )
    anio_epidemiologico_sintoma: Optional[int] = Field(
        None, description="Año epidemiológico del síntoma"
    )

    # Foreign Keys
    id_ciudadano_evento: int = Field(
        foreign_key="ciudadano_evento.id", description="ID del evento del ciudadano"
    )
    id_sintoma: int = Field(
        foreign_key="sintoma.id_snvs_signo_sintoma", description="ID del síntoma"
    )

    # Relaciones
    ciudadano_evento: "CiudadanoEvento" = Relationship(back_populates="sintomas")
    sintoma: "Sintoma" = Relationship(back_populates="detalle_eventos")


class AntecedentesEpidemiologicosEvento(BaseModel, table=True):
    """
    Registro de antecedentes epidemiológicos relevantes para un evento.

    Vincula factores de riesgo o exposiciones previas que pueden estar
    relacionadas con el evento epidemiológico actual.
    """

    __tablename__ = "antecedentes_epidemiologicos_evento"

    # Campos propios
    fecha_antecedente_epidemiologico: Optional[date] = Field(
        None, description="Fecha en que ocurrió el antecedente epidemiológico"
    )

    # Foreign Keys
    id_ciudadano_evento: int = Field(
        foreign_key="ciudadano_evento.id", description="ID del evento del ciudadano"
    )
    id_antecedente_epidemiologico: int = Field(
        foreign_key="antecedente_epidemiologico.id", description="ID del antecedente"
    )

    # Relaciones
    ciudadano_evento: "CiudadanoEvento" = Relationship(back_populates="antecedentes")
    antecedente_epidemiologico_rel: "AntecedenteEpidemiologico" = Relationship(
        back_populates="antecedentes_eventos"
    )

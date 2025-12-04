from datetime import date
from typing import TYPE_CHECKING, Dict, List, Optional

from sqlalchemy import JSON, BigInteger, Column, Index, Text, UniqueConstraint
from sqlmodel import Field, Relationship

from app.core.models import BaseModel

if TYPE_CHECKING:
    from app.domains.atencion_medica.diagnosticos_models import (
        DiagnosticoEvento,
        InternacionEvento,
        TratamientoEvento,
    )
    from app.domains.atencion_medica.investigaciones_models import (
        ContactosNotificacion,
        InvestigacionEvento,
    )
    from app.domains.atencion_medica.salud_models import (
        MuestraEvento,
        Sintoma,
        VacunasCiudadano,
    )
    from app.domains.eventos_epidemiologicos.ambitos_models import (
        AmbitosConcurrenciaEvento,
    )
    from app.domains.eventos_epidemiologicos.clasificacion.models import EventStrategy
    from app.domains.sujetos_epidemiologicos.animales_models import Animal
    from app.domains.sujetos_epidemiologicos.ciudadanos_models import Ciudadano
    from app.domains.territorio.establecimientos_models import Establecimiento
    from app.domains.territorio.geografia_models import Domicilio


class EventoGrupoEno(BaseModel, table=True):
    """
    Tabla de unión para relación many-to-many entre Evento y GrupoEno.

    Permite que un evento epidemiológico pertenezca a múltiples grupos.
    Por ejemplo, un caso de neumonía puede pertenecer tanto al grupo de
    "Infecciones Respiratorias" como al grupo de "Infecciones Invasivas".
    """

    __tablename__ = "evento_grupo_eno"
    __table_args__ = (
        UniqueConstraint('id_evento', 'id_grupo_eno', name='uq_evento_grupo_eno'),
    )

    # Foreign Keys
    id_evento: int = Field(
        foreign_key="evento.id",
        description="ID del evento epidemiológico"
    )
    id_grupo_eno: int = Field(
        foreign_key="grupo_eno.id",
        description="ID del grupo ENO"
    )

    # Relaciones
    evento: "Evento" = Relationship(back_populates="evento_grupos")
    grupo_eno: "GrupoEno" = Relationship(back_populates="grupo_eventos")


class TipoEnoGrupoEno(BaseModel, table=True):
    """
    Tabla de unión para relación many-to-many entre TipoEno y GrupoEno.

    Permite que un tipo de evento epidemiológico pertenezca a múltiples grupos.
    Por ejemplo, "Neumonía" puede pertenecer tanto a "Infecciones Respiratorias"
    como a "Infecciones Invasivas".
    """

    __tablename__ = "tipo_eno_grupo_eno"
    __table_args__ = (
        UniqueConstraint('id_tipo_eno', 'id_grupo_eno', name='uq_tipo_eno_grupo_eno'),
    )

    # Foreign Keys
    id_tipo_eno: int = Field(
        foreign_key="tipo_eno.id",
        description="ID del tipo ENO"
    )
    id_grupo_eno: int = Field(
        foreign_key="grupo_eno.id",
        description="ID del grupo ENO"
    )

    # Relaciones
    tipo_eno: "TipoEno" = Relationship(back_populates="tipo_grupos")
    grupo_eno: "GrupoEno" = Relationship(back_populates="grupo_tipos")


class GrupoEno(BaseModel, table=True):
    """Grupos de eventos epidemiológicos (ENO)"""

    __tablename__ = "grupo_eno"

    # Campos propios
    nombre: str = Field(..., max_length=150, description="Nombre del grupo ENO")
    descripcion: Optional[str] = Field(
        None, max_length=500, description="Descripción del grupo"
    )
    codigo: Optional[str] = Field(
        None, max_length=200, unique=True, index=True, description="Código del grupo"
    )

    # Relaciones
    # Many-to-many con TipoEno a través de TipoEnoGrupoEno
    grupo_tipos: List["TipoEnoGrupoEno"] = Relationship(back_populates="grupo_eno")
    # Many-to-many con Evento a través de EventoGrupoEno
    grupo_eventos: List["EventoGrupoEno"] = Relationship(back_populates="grupo_eno")


class TipoEno(BaseModel, table=True):
    """Tipos de eventos epidemiológicos (ENO)"""

    __tablename__ = "tipo_eno"

    # Campos propios
    nombre: str = Field(..., max_length=200, description="Nombre del tipo ENO")
    descripcion: Optional[str] = Field(
        None, max_length=500, description="Descripción del tipo"
    )
    codigo: Optional[str] = Field(
        None, max_length=200, unique=True, index=True, description="Código del tipo"
    )

    # Relaciones
    # Many-to-many con GrupoEno a través de TipoEnoGrupoEno
    tipo_grupos: List["TipoEnoGrupoEno"] = Relationship(back_populates="tipo_eno")
    eventos: List["Evento"] = Relationship(back_populates="tipo_eno")


class AntecedenteEpidemiologico(BaseModel, table=True):
    """Antecedentes epidemiológicos"""

    __tablename__ = "antecedente_epidemiologico"
    __table_args__ = (
        UniqueConstraint("descripcion", name="uq_antecedente_epidemiologico_descripcion"),
    )

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


class Evento(BaseModel, table=True):
    """Eventos epidemiológicos (instancias específicas de un tipo ENO)"""

    __tablename__ = "evento"
    __table_args__ = (
        # Índice para filtrado por fecha (crítico para mapa temporal)
        Index('idx_evento_fecha_minima', 'fecha_minima_evento'),
        # Índice compuesto para JOIN + filtro fecha
        Index('idx_evento_domicilio_fecha', 'id_domicilio', 'fecha_minima_evento'),
        # Índice compuesto para filtros comunes
        Index('idx_evento_tipo_eno_fecha', 'id_tipo_eno', 'fecha_minima_evento'),
    )

    # Campos propios
    id_evento_caso: int = Field(
        sa_type=BigInteger,
        unique=True,
        index=True,
        description="ID único del evento caso epidemiológico",
    )
    fecha_minima_evento: Optional[date] = Field(
        None, description="Fecha mínima registrada del evento (NULL si no hay fechas válidas)"
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
    fecha_nacimiento: Optional[date] = Field(
        None, description="Fecha de nacimiento del ciudadano al momento de apertura del caso"
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
        None,
        description="Fecha de primera consulta médica del caso (usar NULL cuando sea desconocida)",
    )
    id_origen: Optional[str] = Field(
        None,
        max_length=200,
        description="ID del sistema origen (SNVS, otro sistema, usar 'Desconocido' si no se especifica)",
    )
    semana_epidemiologica_sintomas: Optional[int] = Field(
        None, description="Semana epidemiológica específica de inicio de síntomas"
    )
    semana_epidemiologica_muestra: Optional[int] = Field(
        None, description="Semana epidemiológica específica de toma de muestra"
    )

    # Foreign Keys
    id_tipo_eno: int = Field(foreign_key="tipo_eno.id", description="ID del tipo ENO")
    # NOTA: id_grupo_eno eliminado - ahora se usa relación many-to-many via EventoGrupoEno
    codigo_ciudadano: Optional[int] = Field(
        None,
        sa_type=BigInteger,
        foreign_key="ciudadano.codigo_ciudadano",
        description="Código del ciudadano (opcional si es evento de animal)",
    )
    id_animal: Optional[int] = Field(
        None,
        foreign_key="animal.id",
        description="ID del animal (opcional si es evento de ciudadano)",
    )
    # Agregado por Ignacio - FKs a establecimientos del evento
    id_establecimiento_consulta: Optional[int] = Field(
        None,
        foreign_key="establecimiento.id",
        description="ID del establecimiento donde ocurrió la primera consulta clínica",
    )
    id_establecimiento_notificacion: Optional[int] = Field(
        None,
        foreign_key="establecimiento.id",
        description="ID del establecimiento que notificó/reportó el caso epidemiológico",
    )
    id_establecimiento_carga: Optional[int] = Field(
        None,
        foreign_key="establecimiento.id",
        description="ID del establecimiento donde se cargó el caso en el sistema",
    )

    # Campos para casos ambiguos y metadata
    requiere_revision_especie: Optional[bool] = Field(
        False, description="Indica si requiere revisión manual del tipo de sujeto"
    )
    datos_originales_csv: Optional[Dict] = Field(
        None,
        sa_column=Column(JSON),
        description="Datos originales del CSV para casos ambiguos",
    )
    metadata_clasificacion: Optional[Dict] = Field(
        None,
        sa_column=Column(JSON),
        description="Metadata extraída (fuente_contagio, tipo_sujeto, etc.)",
    )

    # Campos agregados para clasificación con estrategias
    clasificacion_manual: Optional[str] = Field(
        None,
        max_length=500,
        description="Clasificación original del CSV antes del procesamiento",
    )
    clasificacion_estrategia: Optional[str] = Field(
        None,
        max_length=255,
        description="Clasificación aplicada por la estrategia (CONFIRMADOS, SOSPECHOSOS, etc.)",
    )
    metadata_extraida: Optional[Dict] = Field(
        None,
        sa_column=Column(JSON),
        description="Metadata extraída por la estrategia de clasificación",
    )
    confidence_score: Optional[float] = Field(
        None, description="Score de confianza de la clasificación (0-1)"
    )

    # Campos de trazabilidad de clasificación
    id_estrategia_aplicada: Optional[int] = Field(
        None,
        foreign_key="event_strategy.id",
        description="ID de la estrategia que se aplicó para clasificar este evento",
    )
    trazabilidad_clasificacion: Optional[Dict] = Field(
        None,
        sa_column=Column(JSON),
        description="Trazabilidad completa de la clasificación: reglas evaluadas, condiciones cumplidas, razón de la clasificación",
    )

    # Domicilio del evento (INMUTABLE - donde ocurrió el caso)
    id_domicilio: Optional[int] = Field(
        None,
        foreign_key="domicilio.id",
        index=True,
        description="ID del domicilio donde ocurrió el evento (inmutable, permite clusters)",
    )

    # Relaciones
    tipo_eno: "TipoEno" = Relationship(back_populates="eventos")
    # Many-to-many con GrupoEno a través de EventoGrupoEno
    evento_grupos: List["EventoGrupoEno"] = Relationship(back_populates="evento")
    ciudadano: Optional["Ciudadano"] = Relationship(back_populates="eventos")
    animal: Optional["Animal"] = Relationship(back_populates="eventos")
    estrategia_aplicada: Optional["EventStrategy"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Evento.id_estrategia_aplicada]"}
    )
    # Agregado por Ignacio - Relaciones con establecimientos
    establecimiento_consulta: Optional["Establecimiento"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Evento.id_establecimiento_consulta]"}
    )
    establecimiento_notificacion: Optional["Establecimiento"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[Evento.id_establecimiento_notificacion]"
        }
    )
    establecimiento_carga: Optional["Establecimiento"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Evento.id_establecimiento_carga]"}
    )
    sintomas: List["DetalleEventoSintomas"] = Relationship(back_populates="evento")
    muestras: List["MuestraEvento"] = Relationship(back_populates="evento")
    antecedentes: List["AntecedentesEpidemiologicosEvento"] = Relationship(
        back_populates="evento"
    )
    vacunas: List["VacunasCiudadano"] = Relationship(back_populates="evento")
    diagnosticos: List["DiagnosticoEvento"] = Relationship(back_populates="evento")
    internaciones: List["InternacionEvento"] = Relationship(back_populates="evento")
    # Nota: estudios ahora están relacionados con MuestraEvento, no directamente con Evento
    tratamientos: List["TratamientoEvento"] = Relationship(back_populates="evento")
    investigaciones: List["InvestigacionEvento"] = Relationship(back_populates="evento")
    contactos: List["ContactosNotificacion"] = Relationship(back_populates="evento")
    ambitos_concurrencia: List["AmbitosConcurrenciaEvento"] = Relationship(
        back_populates="evento"
    )
    # Domicilio del evento (inmutable)
    domicilio: Optional["Domicilio"] = Relationship(back_populates="eventos")


class DetalleEventoSintomas(BaseModel, table=True):
    """
    Detalle de síntomas específicos presentados durante un evento epidemiológico.

    Permite registrar múltiples síntomas por evento con sus fechas correspondientes.
    """

    __tablename__ = "detalle_evento_sintomas"
    __table_args__ = (
        UniqueConstraint('id_evento', 'id_sintoma', name='uq_evento_sintoma'),
    )

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
    id_evento: int = Field(foreign_key="evento.id", description="ID del evento")
    id_sintoma: int = Field(foreign_key="sintoma.id", description="ID del síntoma")

    # Relaciones
    evento: "Evento" = Relationship(back_populates="sintomas")
    sintoma: "Sintoma" = Relationship(back_populates="detalle_eventos")


class AntecedentesEpidemiologicosEvento(BaseModel, table=True):
    """
    Registro de antecedentes epidemiológicos relevantes para un evento.

    Vincula factores de riesgo o exposiciones previas que pueden estar
    relacionadas con el evento epidemiológico actual.
    """

    __tablename__ = "antecedentes_epidemiologicos_evento"
    __table_args__ = (
        UniqueConstraint('id_evento', 'id_antecedente_epidemiologico', name='uq_evento_antecedente'),
    )

    # Campos propios
    fecha_antecedente_epidemiologico: Optional[date] = Field(
        None, description="Fecha en que ocurrió el antecedente epidemiológico"
    )

    # Foreign Keys
    id_evento: int = Field(foreign_key="evento.id", description="ID del evento")
    id_antecedente_epidemiologico: int = Field(
        foreign_key="antecedente_epidemiologico.id", description="ID del antecedente"
    )

    # Relaciones
    evento: "Evento" = Relationship(back_populates="antecedentes")
    antecedente_epidemiologico_rel: "AntecedenteEpidemiologico" = Relationship(
        back_populates="antecedentes_eventos"
    )

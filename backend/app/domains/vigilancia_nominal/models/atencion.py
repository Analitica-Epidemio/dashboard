"""
Modelos de atención médica para casos de vigilancia nominal.

Incluye:
- DiagnosticoCasoEpidemiologico: Diagnósticos realizados
- InternacionCasoEpidemiologico: Internaciones hospitalarias
- TratamientoCasoEpidemiologico: Tratamientos aplicados
- InvestigacionCasoEpidemiologico: Investigaciones epidemiológicas
- ContactosNotificacion: Contactos relevados

Todos estos modelos son extensiones del CasoEpidemiologico.
"""

from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Text, UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlmodel import Field, Relationship

from app.core.constants import OrigenFinanciamiento
from app.core.models import BaseModel

if TYPE_CHECKING:
    from app.domains.territorio.establecimientos_models import Establecimiento
    from app.domains.vigilancia_nominal.models.caso import CasoEpidemiologico


# =============================================================================
# DIAGNÓSTICOS
# =============================================================================


class DiagnosticoCasoEpidemiologico(BaseModel, table=True):
    """
    Diagnósticos de casos epidemiológicos.

    Almacena información sobre los diagnósticos realizados,
    incluyendo clasificaciones manuales y automáticas.
    """

    __tablename__ = "diagnostico_caso_epidemiologico"
    __table_args__ = (
        UniqueConstraint("id_caso", name="uq_diagnostico_caso"),
        {"extend_existing": True},
    )

    # Campos propios
    clasificacion_manual: str = Field(
        ..., max_length=150, description="Clasificación manual del diagnóstico"
    )
    clasificacion_automatica: Optional[str] = Field(
        None, max_length=150, description="Clasificación automática"
    )
    clasificacion_algoritmo: Optional[str] = Field(
        None, max_length=150, description="Algoritmo de clasificación"
    )
    validacion: Optional[str] = Field(
        None,
        max_length=500,
        description="Estado de validación del diagnóstico",
    )
    edad_diagnostico: Optional[int] = Field(
        None, description="Edad al momento del diagnóstico"
    )
    grupo_etario: Optional[str] = Field(
        None, max_length=150, description="Grupo etario"
    )
    diagnostico_referido: Optional[str] = Field(
        None,
        max_length=150,
        description="Diagnóstico referido",
    )
    fecha_diagnostico_referido: Optional[date] = Field(
        None, description="Fecha del diagnóstico referido"
    )

    # Foreign Keys
    id_caso: int = Field(
        foreign_key="caso_epidemiologico.id", description="ID del caso"
    )
    id_establecimiento_diagnostico: Optional[int] = Field(
        None,
        foreign_key="establecimiento.id",
        description="ID del establecimiento donde se realizó el diagnóstico",
    )

    # Relaciones
    caso: Mapped["CasoEpidemiologico"] = Relationship(back_populates="diagnosticos")
    establecimiento: Mapped[Optional["Establecimiento"]] = Relationship(
        back_populates="diagnosticos"
    )


# =============================================================================
# INTERNACIONES
# =============================================================================


class InternacionCasoEpidemiologico(BaseModel, table=True):
    """
    Registro de internaciones hospitalarias durante casos epidemiológicos.

    Rastrea el estado de internación de pacientes, incluyendo fechas,
    cuidados intensivos, altas médicas y fallecimientos.
    """

    __tablename__ = "internacion_caso_epidemiologico"
    __table_args__ = (
        UniqueConstraint("id_caso", name="uq_internacion_caso"),
        {"extend_existing": True},
    )

    fue_internado: Optional[bool] = Field(None, description="Fue internado")
    fue_curado: Optional[bool] = Field(None, description="Fue curado")
    requirio_cuidado_intensivo: Optional[bool] = Field(
        None, description="Requirió cuidado intensivo"
    )
    fecha_internacion: Optional[date] = Field(None, description="Fecha de internación")
    fecha_cuidados_intensivos: Optional[date] = Field(
        None, description="Fecha de ingreso a cuidados intensivos"
    )
    establecimiento_internacion: Optional[str] = Field(
        None,
        max_length=150,
        description="Establecimiento de internación (texto libre)",
    )
    fecha_alta_medica: Optional[date] = Field(None, description="Fecha de alta médica")
    es_fallecido: Optional[bool] = Field(None, description="Falleció")
    fecha_fallecimiento: Optional[date] = Field(
        None, description="Fecha de fallecimiento"
    )

    # Foreign Keys
    id_caso: int = Field(
        foreign_key="caso_epidemiologico.id", description="ID del caso"
    )

    # Relaciones
    caso: Mapped["CasoEpidemiologico"] = Relationship(back_populates="internaciones")


# =============================================================================
# TRATAMIENTOS
# =============================================================================


class TratamientoCasoEpidemiologico(BaseModel, table=True):
    """
    Tratamientos médicos aplicados durante casos epidemiológicos.

    Documenta los tratamientos administrados a pacientes.
    """

    __tablename__ = "tratamiento_caso_epidemiologico"
    __table_args__ = (
        UniqueConstraint(
            "id_caso",
            "descripcion_tratamiento",
            "fecha_inicio_tratamiento",
            name="uq_tratamiento_caso",
        ),
        {"extend_existing": True},
    )

    establecimiento_tratamiento: Optional[str] = Field(
        None, max_length=150, description="Establecimiento de tratamiento (texto libre)"
    )
    descripcion_tratamiento: Optional[str] = Field(
        None, max_length=150, description="Descripción del tratamiento"
    )
    fecha_inicio_tratamiento: Optional[date] = Field(
        None, description="Fecha de inicio del tratamiento"
    )
    fecha_fin_tratamiento: Optional[date] = Field(
        None, description="Fecha de fin del tratamiento"
    )
    resultado_tratamiento: Optional[str] = Field(
        None, description="Resultado del tratamiento"
    )

    # Foreign Keys
    id_caso: int = Field(
        foreign_key="caso_epidemiologico.id", description="ID del caso"
    )
    id_establecimiento_tratamiento: Optional[int] = Field(
        None,
        foreign_key="establecimiento.id",
        description="ID del establecimiento donde se realizó el tratamiento",
    )

    # Relaciones
    caso: Mapped["CasoEpidemiologico"] = Relationship(back_populates="tratamientos")
    establecimiento: Mapped[Optional["Establecimiento"]] = Relationship()


# =============================================================================
# INVESTIGACIONES EPIDEMIOLÓGICAS
# =============================================================================


class InvestigacionCasoEpidemiologico(BaseModel, table=True):
    """
    Investigaciones epidemiológicas de casos.

    Registra información sobre investigaciones en terreno,
    eventos centinela y participación de usuarios.
    """

    __tablename__ = "investigacion_caso_epidemiologico"
    __table_args__ = (UniqueConstraint("id_caso", name="uq_investigacion_caso"),)

    es_usuario_centinela: Optional[bool] = Field(None, description="Usuario centinela")
    es_evento_centinela: Optional[bool] = Field(None, description="Caso centinela")
    id_usuario_registro: Optional[int] = Field(
        None, description="ID del usuario que registró"
    )
    participo_usuario_centinela: Optional[bool] = Field(
        None, description="Usuario centinela participó"
    )
    id_usuario_centinela_participante: Optional[int] = Field(
        None, description="ID del usuario centinela que participó"
    )
    id_snvs_caso: Optional[int] = Field(None, description="ID SNVS del caso")
    es_investigacion_terreno: Optional[bool] = Field(
        None, description="Investigación en terreno"
    )
    fecha_investigacion: Optional[date] = Field(
        None, description="Fecha de la investigación"
    )
    tipo_y_lugar_investigacion: Optional[str] = Field(
        None, sa_type=Text, description="Tipo y lugar de investigación"
    )
    origen_financiamiento: Optional[OrigenFinanciamiento] = Field(
        None, description="Origen del financiamiento"
    )

    # Foreign Keys
    id_caso: int = Field(
        foreign_key="caso_epidemiologico.id", description="ID del caso"
    )

    # Relaciones
    caso: Mapped["CasoEpidemiologico"] = Relationship(back_populates="investigaciones")


# =============================================================================
# CONTACTOS
# =============================================================================


class ContactosNotificacion(BaseModel, table=True):
    """
    Registro de contactos relevados durante la investigación epidemiológica.

    Documenta contactos con casos confirmados o sospechosos,
    y características demográficas de los contactos.
    """

    __tablename__ = "contactos_notificacion"
    __table_args__ = (UniqueConstraint("id_caso", name="uq_contactos_caso"),)

    hubo_contacto_con_caso_confirmado: Optional[bool] = Field(
        None, description="Contacto con caso confirmado"
    )
    hubo_contacto_con_caso_sospechoso: Optional[bool] = Field(
        None, description="Contacto con caso sospechoso"
    )
    contactos_relevados_contactos_detectados: Optional[str] = Field(
        None, max_length=32, description="Contactos relevados/detectados"
    )
    cantidad_contactos_menores_un_anio: Optional[int] = Field(
        None, ge=0, description="Contactos menores de 1 año"
    )
    cantidad_contactos_vacunados: Optional[int] = Field(
        None, ge=0, description="Contactos vacunados"
    )
    cantidad_contactos_embarazadas: Optional[int] = Field(
        None, ge=0, description="Contactos embarazadas"
    )

    # Foreign Keys
    id_caso: int = Field(
        foreign_key="caso_epidemiologico.id", description="ID del caso"
    )

    # Relaciones
    caso: Mapped["CasoEpidemiologico"] = Relationship(back_populates="contactos")

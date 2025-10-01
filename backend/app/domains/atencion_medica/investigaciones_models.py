"""Modelos relacionados con investigaciones epidemiológicas y contactos."""

from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Text, UniqueConstraint
from sqlmodel import Field, Relationship

from app.core.models import BaseModel
from app.core.shared.enums import OrigenFinanciamiento

if TYPE_CHECKING:
    from app.domains.eventos_epidemiologicos.eventos.models import Evento


class InvestigacionEvento(BaseModel, table=True):
    """
    Investigaciones epidemiológicas de eventos.

    Registra información sobre investigaciones en terreno, eventos centinela,
    participación de usuarios y financiamiento de las investigaciones.
    """

    __tablename__ = "investigacion_evento"
    __table_args__ = (
        UniqueConstraint('id_evento', name='uq_investigacion_evento'),
    )

    # Campos propios
    # TODO: id_usuario_centinela_participante esos deberían ser fk???? Consultar con luciano
    es_usuario_centinela: Optional[bool] = Field(None, description="Usuario centinela")
    es_evento_centinela: Optional[bool] = Field(None, description="Evento centinela")
    id_usuario_registro: Optional[int] = Field(
        None, description="ID del usuario que registró"
    )
    participo_usuario_centinela: Optional[bool] = Field(
        None, description="Usuario centinela participó"
    )
    id_usuario_centinela_participante: Optional[int] = Field(
        None, description="ID del usuario centinela que participó"
    )
    # Agregado por Ignacio - Campo SISTEMA faltante del CSV
    id_snvs_evento: Optional[int] = Field(
        None, description="ID SNVS del evento (diferente del ID_SNVS_EVENTO_MUESTRA)"
    )
    es_investigacion_terreno: Optional[bool] = Field(
        None, description="Investigación en terreno"
    )
    fecha_investigacion: Optional[date] = Field(
        None, description="Fecha de la investigación"
    )
    tipo_y_lugar_investigacion: Optional[str] = Field(
        None, sa_column=Text, description="Tipo y lugar de investigación"
    )
    origen_financiamiento: Optional[OrigenFinanciamiento] = Field(
        None, description="Origen del financiamiento"
    )

    # Foreign Keys
    id_evento: int = Field(foreign_key="evento.id", description="ID del evento")

    # Relaciones
    evento: "Evento" = Relationship(back_populates="investigaciones")


class ContactosNotificacion(BaseModel, table=True):
    """
    Registro de contactos y notificaciones de eventos epidemiológicos.

    Documenta los contactos relevados durante la investigación epidemiológica,
    incluyendo contactos con casos confirmados o sospechosos, y características
    demográficas de los contactos (menores, vacunados, embarazadas).
    """

    __tablename__ = "contactos_notificacion"
    __table_args__ = (
        UniqueConstraint('id_evento', name='uq_contactos_evento'),
    )

    # Campos propios
    hubo_contacto_con_caso_confirmado: Optional[bool] = Field(
        None, description="Contacto con caso confirmado"
    )
    hubo_contacto_con_caso_sospechoso: Optional[bool] = Field(
        None, description="Contacto con caso sospechoso"
    )
    # TODO: IMPORTANTE - Campo problemático con datos mixtos:
    # Luciano ponia algo como
    # - CONTACTOS_RELEVADOS_CONTACTOS_DETECTADOS
    # - Debería ser numérico pero hay valores como "6/0"
    # - Hay errores de parseo donde se interpretó como fecha "07-01-2024"
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
    id_evento: int = Field(foreign_key="evento.id", description="ID del evento")

    # Relaciones
    evento: "Evento" = Relationship(back_populates="contactos")

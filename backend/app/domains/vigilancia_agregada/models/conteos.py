"""
Modelos de conteos de vigilancia pasiva.

Cada conteo representa una línea de detalle dentro de una NotificacionSemanal,
desglosando cantidades por evento y demografía.

Tipos de conteos:
- ConteoCasosClinicos: Casos clínicos (CLI_P26) - ETI, Neumonía, etc.
- ConteoEstudiosLab: Estudios de laboratorio (LAB_P26) - estudiadas + positivas
- ConteoCamasIRA: Internaciones por IRA (CLI_P26_INT) - camas, UTI, ARM
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import model_validator
from sqlalchemy import BigInteger, Index, SmallInteger
from sqlmodel import Field, Relationship

from app.core.models import BaseModel
from app.domains.vigilancia_agregada.constants import Sexo

if TYPE_CHECKING:
    from app.domains.catalogos.agentes.models import AgenteEtiologico
    from app.domains.vigilancia_agregada.models.cargas import NotificacionSemanal
    from app.domains.vigilancia_agregada.models.catalogos import (
        RangoEtario,
        TipoCasoEpidemiologicoPasivo,
    )


class ConteoCasosClinicos(BaseModel, table=True):
    """
    Conteo de casos clínicos de vigilancia pasiva (CLI_P26).

    Cada registro representa la cantidad de casos de un evento
    específico para una combinación de demografía en una semana.

    Ejemplo:
        "47 casos de ETI en mujeres de 15-24 años, residentes, ambulatorias"

    Attributes:
        id_snvs: ID de la línea en SNVS (ID_AGRP_CLINICA)
        cantidad: Número de casos reportados
        tipo_evento_id: Referencia al tipo de evento (ETI, Neumonía, etc.)
        rango_etario_id: Referencia al grupo de edad
        sexo: Sexo biológico (M/F/X)
    """

    __tablename__ = "conteo_casos_clinicos"
    __table_args__ = (
        Index("ix_conteo_cli_evento", "tipo_evento_id"),
        Index("ix_conteo_cli_notif", "notificacion_id"),
        Index("ix_conteo_cli_analytics", "notificacion_id", "tipo_evento_id"),
    )

    # ═══════════════════════════════════════════════════════════════
    # Identificación SNVS
    # ═══════════════════════════════════════════════════════════════

    id_snvs: int = Field(
        ...,
        sa_type=BigInteger,
        index=True,
        description="ID de la línea en SNVS (ID_AGRP_CLINICA)",
    )

    # ═══════════════════════════════════════════════════════════════
    # Métrica principal
    # ═══════════════════════════════════════════════════════════════

    cantidad: int = Field(
        ...,
        ge=0,
        sa_type=SmallInteger,
        description="Cantidad de casos reportados (CANTIDAD). Rango típico: 0-253",
    )

    # ═══════════════════════════════════════════════════════════════
    # Demografía
    # ═══════════════════════════════════════════════════════════════

    sexo: Sexo = Field(
        ...,
        description="Sexo biológico (M=Masculino, F=Femenino, X=Sin especificar)",
    )

    es_residente: bool = Field(
        default=True,
        description="Si es residente de la jurisdicción (RESIDENTE)",
    )

    es_ambulatorio: bool = Field(
        default=True,
        description="Si fue atención ambulatoria vs internado (AMBULATORIO)",
    )

    # ═══════════════════════════════════════════════════════════════
    # Auditoría SNVS
    # ═══════════════════════════════════════════════════════════════

    fecha_registro_snvs: Optional[datetime] = Field(
        None,
        description="Fecha de registro de la línea (FECHAREGISTROCLINICA)",
    )

    usuario_snvs: Optional[str] = Field(
        None,
        max_length=200,
        description="Usuario que registró (USERREGISTROCLINICA)",
    )

    # ═══════════════════════════════════════════════════════════════
    # Foreign Keys
    # ═══════════════════════════════════════════════════════════════

    notificacion_id: int = Field(
        ...,
        foreign_key="notificacion_semanal.id",
        index=True,
        description="ID de la notificación semanal (encabezado)",
    )

    tipo_evento_id: int = Field(
        ...,
        foreign_key="tipo_evento_pasivo.id",
        index=True,
        description="ID del tipo de evento (ETI, Neumonía, etc.)",
    )

    rango_etario_id: int = Field(
        ...,
        foreign_key="rango_etario.id",
        index=True,
        description="ID del rango de edad",
    )

    # ═══════════════════════════════════════════════════════════════
    # Relaciones
    # ═══════════════════════════════════════════════════════════════

    notificacion: "NotificacionSemanal" = Relationship(
        back_populates="conteos_clinicos"
    )
    tipo_evento: "TipoCasoEpidemiologicoPasivo" = Relationship(
        back_populates="conteos_clinicos"
    )
    rango_etario: "RangoEtario" = Relationship(
        back_populates="conteos_clinicos"
    )


class ConteoEstudiosLab(BaseModel, table=True):
    """
    Conteo de estudios de laboratorio de vigilancia pasiva (LAB_P26).

    A diferencia de los casos clínicos, laboratorio reporta dos métricas:
    - estudiadas: Cantidad de muestras analizadas
    - positivas: Cantidad de resultados positivos

    Ejemplo:
        "122 muestras estudiadas, 47 positivas para Rotavirus"

    La tasa de positividad se puede calcular como: positivas / estudiadas

    Los datos de laboratorio referencian a AgenteEtiologico (patogenos) del
    catalogo compartido, NO a TipoCasoEpidemiologicoPasivo.

    Attributes:
        estudiadas: Muestras analizadas para este agente/demografía
        positivas: Resultados positivos encontrados
        id_agente: Referencia al agente etiologico (VSR, Rotavirus, etc.)
    """

    __tablename__ = "conteo_estudios_lab"
    __table_args__ = (
        Index("ix_conteo_lab_agente", "id_agente"),
        Index("ix_conteo_lab_notif", "notificacion_id"),
        Index("ix_conteo_lab_analytics", "notificacion_id", "id_agente"),
    )

    # ═══════════════════════════════════════════════════════════════
    # Identificación SNVS
    # ═══════════════════════════════════════════════════════════════

    id_snvs: int = Field(
        ...,
        sa_type=BigInteger,
        index=True,
        description="ID de la línea en SNVS (ID_AGRP_LABO)",
    )

    # ═══════════════════════════════════════════════════════════════
    # Métricas de laboratorio
    # ═══════════════════════════════════════════════════════════════

    estudiadas: int = Field(
        default=0,
        ge=0,
        description="Cantidad de muestras estudiadas (ESTUDIADAS)",
    )

    positivas: int = Field(
        default=0,
        ge=0,
        sa_type=SmallInteger,
        description="Cantidad de resultados positivos (POSITIVAS)",
    )

    # ═══════════════════════════════════════════════════════════════
    # Demografía
    # ═══════════════════════════════════════════════════════════════

    sexo: Sexo = Field(
        ...,
        description="Sexo biológico",
    )

    es_residente: bool = Field(
        default=True,
        description="Si es residente de la jurisdicción",
    )

    es_ambulatorio: bool = Field(
        default=True,
        description="Si fue atención ambulatoria",
    )

    # ═══════════════════════════════════════════════════════════════
    # Auditoría SNVS
    # ═══════════════════════════════════════════════════════════════

    fecha_registro_snvs: Optional[datetime] = Field(
        None,
        description="Fecha de registro (FECHA_REGISTRO1)",
    )

    fecha_modificacion_snvs: Optional[datetime] = Field(
        None,
        description="Fecha de última modificación (FECHA_MODIFICACION)",
    )

    usuario_snvs: Optional[str] = Field(
        None,
        max_length=200,
        description="Usuario que registró (USER_REGISTRO)",
    )

    # ═══════════════════════════════════════════════════════════════
    # Foreign Keys
    # ═══════════════════════════════════════════════════════════════

    notificacion_id: int = Field(
        ...,
        foreign_key="notificacion_semanal.id",
        index=True,
        description="ID de la notificación semanal",
    )

    id_agente: int = Field(
        ...,
        foreign_key="agente_etiologico.id",
        index=True,
        description="ID del agente etiologico (VSR, Rotavirus, Salmonella, etc.)",
    )

    rango_etario_id: int = Field(
        ...,
        foreign_key="rango_etario.id",
        index=True,
        description="ID del rango de edad",
    )

    # ═══════════════════════════════════════════════════════════════
    # Validators
    # ═══════════════════════════════════════════════════════════════

    @model_validator(mode="after")
    def positivas_no_mayor_que_estudiadas(self) -> "ConteoEstudiosLab":
        """Valida que positivas <= estudiadas."""
        # Verificar que ambos valores estén definidos (SQLModel puede tener None temporalmente)
        if self.positivas is not None and self.estudiadas is not None:
            if self.positivas > self.estudiadas:
                raise ValueError(
                    f"positivas ({self.positivas}) no puede ser mayor que "
                    f"estudiadas ({self.estudiadas})"
                )
        return self

    # ═══════════════════════════════════════════════════════════════
    # Propiedades computadas
    # ═══════════════════════════════════════════════════════════════

    @property
    def tasa_positividad(self) -> Optional[float]:
        """
        Calcula la tasa de positividad (0-1).

        Returns:
            float entre 0 y 1, o None si estudiadas == 0
        """
        if self.estudiadas == 0:
            return None
        return self.positivas / self.estudiadas

    @property
    def tasa_positividad_porcentaje(self) -> Optional[float]:
        """
        Calcula la tasa de positividad como porcentaje (0-100).

        Returns:
            float entre 0 y 100, o None si estudiadas == 0
        """
        tasa = self.tasa_positividad
        return tasa * 100 if tasa is not None else None

    # ═══════════════════════════════════════════════════════════════
    # Relaciones
    # ═══════════════════════════════════════════════════════════════

    notificacion: "NotificacionSemanal" = Relationship(
        back_populates="conteos_laboratorio"
    )
    agente: "AgenteEtiologico" = Relationship()
    rango_etario: "RangoEtario" = Relationship(
        back_populates="conteos_laboratorio"
    )


class ConteoCamasIRA(BaseModel, table=True):
    """
    Conteo de internaciones por IRA de vigilancia pasiva (CLI_P26_INT).

    CasoEpidemiologicos específicos de capacidad hospitalaria e internaciones:
    - Pacientes en ARM (Asistencia Respiratoria Mecánica) por IRA
    - Pacientes en UTI (Unidad de Terapia Intensiva) por IRA
    - Pacientes en internación general por IRA
    - Dotación de camas/UTI (capacidad instalada)
    - Camas/UTI ocupadas por todas las causas

    Los grupos de edad son simplificados respecto a clínico:
    - Adultos <60 años
    - Adultos >=60 años
    - Pediátricos <3 años
    - Pediátricos >=3 años
    - Sin especificar

    Attributes:
        cantidad: Número reportado (pacientes, camas, etc.)
        tipo_evento_id: Tipo de métrica (ARM, UTI, camas, etc.)
    """

    __tablename__ = "conteo_camas_ira"
    __table_args__ = (
        Index("ix_conteo_int_evento", "tipo_evento_id"),
        Index("ix_conteo_int_notif", "notificacion_id"),
        Index("ix_conteo_int_analytics", "notificacion_id", "tipo_evento_id"),
    )

    # ═══════════════════════════════════════════════════════════════
    # Identificación SNVS
    # ═══════════════════════════════════════════════════════════════

    id_snvs: int = Field(
        ...,
        sa_type=BigInteger,
        index=True,
        description="ID de la línea en SNVS (ID_AGRP_CLINICA)",
    )

    # ═══════════════════════════════════════════════════════════════
    # Métrica
    # ═══════════════════════════════════════════════════════════════

    cantidad: int = Field(
        ...,
        ge=0,
        sa_type=SmallInteger,
        description="Cantidad reportada (pacientes, camas, etc.). Rango típico: 0-137",
    )

    # ═══════════════════════════════════════════════════════════════
    # Demografía (simplificada para internaciones)
    # ═══════════════════════════════════════════════════════════════

    sexo: Sexo = Field(
        ...,
        description="Sexo biológico",
    )

    # ═══════════════════════════════════════════════════════════════
    # Auditoría SNVS
    # ═══════════════════════════════════════════════════════════════

    fecha_registro_snvs: Optional[datetime] = Field(
        None,
        description="Fecha de registro de la línea",
    )

    usuario_snvs: Optional[str] = Field(
        None,
        max_length=200,
        description="Usuario que registró",
    )

    # ═══════════════════════════════════════════════════════════════
    # Foreign Keys
    # ═══════════════════════════════════════════════════════════════

    notificacion_id: int = Field(
        ...,
        foreign_key="notificacion_semanal.id",
        index=True,
        description="ID de la notificación semanal",
    )

    tipo_evento_id: int = Field(
        ...,
        foreign_key="tipo_evento_pasivo.id",
        index=True,
        description="ID del tipo de evento (ARM, UTI, camas, etc.)",
    )

    rango_etario_id: int = Field(
        ...,
        foreign_key="rango_etario.id",
        index=True,
        description="ID del rango de edad (simplificado)",
    )

    # ═══════════════════════════════════════════════════════════════
    # Relaciones
    # ═══════════════════════════════════════════════════════════════

    notificacion: "NotificacionSemanal" = Relationship(
        back_populates="conteos_internacion"
    )
    tipo_evento: "TipoCasoEpidemiologicoPasivo" = Relationship(
        back_populates="conteos_internacion"
    )
    rango_etario: "RangoEtario" = Relationship(
        back_populates="conteos_internacion"
    )

"""
Modelos de datamarts para análisis y reporting.

Estos modelos están optimizados para consultas rápidas con:
- Datos desnormalizados
- Índices en campos de búsqueda frecuente
- Agregaciones pre-calculadas
"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import BigInteger, Index, Text
from sqlmodel import Field

from app.core.models import BaseModel


class DatamartEpidemiologia(BaseModel, table=True):
    """
    Datamart desnormalizado para análisis epidemiológico rápido.

    Contiene todos los datos relevantes en una sola tabla para minimizar JOINs
    y optimizar el rendimiento de consultas analíticas.
    """

    __tablename__ = "datamart_epidemiologia"
    __table_args__ = (
        # Índices compuestos para queries frecuentes
        Index("idx_datamart_fecha_evento", "fecha_inicio_sintomas", "anio_evento"),
        Index(
            "idx_datamart_localidad_fecha",
            "id_localidad_indec",
            "fecha_inicio_sintomas",
        ),
        Index("idx_datamart_evento_fecha", "id_evento", "fecha_inicio_sintomas"),
        Index("idx_datamart_clasificacion", "clasificacion_resumen"),
        Index(
            "idx_datamart_semana_epi",
            "anio_epidemiologico_apertura",
            "semana_epidemiologica_apertura",
        ),
    )

    # IDs de referencia (no FKs para evitar dependencias)
    id_evento_caso: int = Field(
        sa_type=BigInteger,
        unique=True,
        index=True,
        description="ID único del evento caso epidemiológico",
    )
    codigo_ciudadano: int = Field(
        sa_type=BigInteger, index=True, description="Código del ciudadano"
    )
    id_evento: Optional[int] = Field(
        None, index=True, description="ID del tipo de evento"
    )

    # Datos del ciudadano (desnormalizados)
    dni_ciudadano: Optional[str] = Field(
        None, max_length=20, index=True, description="DNI del ciudadano"
    )
    nombre_completo: Optional[str] = Field(
        None, max_length=200, description="Nombre completo del ciudadano"
    )
    fecha_nacimiento: Optional[date] = Field(None, description="Fecha de nacimiento")
    sexo: Optional[str] = Field(None, max_length=20, description="Sexo del ciudadano")

    # Datos geográficos (desnormalizados)
    id_localidad_indec: Optional[int] = Field(
        None, index=True, description="ID INDEC de la localidad"
    )
    nombre_localidad: Optional[str] = Field(
        None, max_length=150, description="Nombre de la localidad"
    )
    nombre_departamento: Optional[str] = Field(
        None, max_length=150, description="Nombre del departamento"
    )
    region_sanitaria: Optional[str] = Field(
        None, max_length=50, index=True, description="Región sanitaria"
    )

    # Datos del evento
    nombre_evento: Optional[str] = Field(
        None, max_length=200, description="Nombre del evento epidemiológico"
    )
    grupo_evento: Optional[str] = Field(
        None, max_length=150, index=True, description="Grupo del evento"
    )
    fecha_inicio_sintomas: Optional[date] = Field(
        None, index=True, description="Fecha de inicio de síntomas"
    )
    fecha_apertura_caso: Optional[date] = Field(
        None, index=True, description="Fecha de apertura del caso"
    )
    semana_epidemiologica_apertura: Optional[int] = Field(
        None, description="Semana epidemiológica de apertura"
    )
    anio_epidemiologico_apertura: Optional[int] = Field(
        None, description="Año epidemiológico de apertura"
    )
    anio_evento: Optional[int] = Field(None, index=True, description="Año del evento")

    # Datos clínicos agregados
    clasificacion_resumen: Optional[str] = Field(
        None, max_length=100, index=True, description="Clasificación resumida del caso"
    )
    es_caso_sintomatico: Optional[bool] = Field(
        None, description="Indica si es caso sintomático"
    )
    cantidad_sintomas: Optional[int] = Field(
        None, description="Cantidad de síntomas registrados"
    )
    sintomas_principales: Optional[str] = Field(
        None, sa_type=Text, description="Lista de síntomas principales (JSON)"
    )

    # Datos de laboratorio agregados
    cantidad_muestras: Optional[int] = Field(
        None, description="Cantidad de muestras tomadas"
    )
    resultado_final: Optional[str] = Field(
        None, max_length=100, index=True, description="Resultado final del laboratorio"
    )
    fecha_resultado: Optional[date] = Field(
        None, description="Fecha del resultado final"
    )

    # Datos de internación
    fue_internado: Optional[bool] = Field(
        None, index=True, description="Indica si fue internado"
    )
    dias_internacion: Optional[int] = Field(
        None, description="Total de días de internación"
    )
    requirio_uti: Optional[bool] = Field(None, description="Indica si requirió UTI")

    # Datos de evolución
    evolucion_final: Optional[str] = Field(
        None, max_length=50, index=True, description="Evolución final del caso"
    )
    fecha_alta: Optional[date] = Field(None, description="Fecha de alta")

    # Metadatos para optimización
    ultima_actualizacion_datamart: datetime = Field(
        default_factory=datetime.now,
        description="Última actualización del registro en el datamart",
    )
    hash_cambios: Optional[str] = Field(
        None,
        max_length=64,
        description="Hash para detectar cambios en los datos origen",
    )

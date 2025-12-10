"""
Builder para métricas de ocupación hospitalaria (CLI_P26_INT).

Construye queries sobre ConteoCamasIRA con los JOINs necesarios.
"""

from sqlmodel import col, select

from app.domains.metricas.registry.dimensions import DimensionCode
from app.domains.metricas.registry.metrics import MetricDefinition
from app.domains.territorio.establecimientos_models import Establecimiento
from app.domains.territorio.geografia_models import (
    Departamento,
    Localidad,
    Provincia,
)
from app.domains.vigilancia_agregada.models.cargas import NotificacionSemanal
from app.domains.vigilancia_agregada.models.catalogos import (
    RangoEtario,
    TipoCasoEpidemiologicoPasivo,
)
from app.domains.vigilancia_agregada.models.conteos import ConteoCamasIRA

from .base import MetricQueryBuilder


class HospitalarioQueryBuilder(MetricQueryBuilder):
    """
    Builder para queries sobre ConteoCamasIRA.

    Incluye JOINs necesarios para:
    - NotificacionSemanal (tiempo, establecimiento)
    - TipoCasoEpidemiologicoPasivo (ARM, UTI, camas, etc.)
    - RangoEtario (grupo de edad simplificado)
    - Geografía (establecimiento -> localidad -> departamento -> provincia)
    """

    def get_dimension_column(self, dim_code: DimensionCode):
        """Mapeo de dimensiones a columnas SQL."""
        return {
            DimensionCode.SEMANA_EPIDEMIOLOGICA: NotificacionSemanal.semana,
            DimensionCode.ANIO_EPIDEMIOLOGICO: NotificacionSemanal.anio,
            DimensionCode.TIPO_EVENTO: TipoCasoEpidemiologicoPasivo.nombre,
            DimensionCode.GRUPO_ETARIO: RangoEtario.nombre,
            DimensionCode.SEXO: ConteoCamasIRA.sexo,
            DimensionCode.PROVINCIA: Provincia.nombre,
            DimensionCode.DEPARTAMENTO: Departamento.nombre,
            DimensionCode.ESTABLECIMIENTO: Establecimiento.nombre,
        }[dim_code]

    def get_dimension_order_column(self, dim_code: DimensionCode):
        """Columna de orden (GRUPO_ETARIO usa RangoEtario.orden)."""
        if dim_code == DimensionCode.GRUPO_ETARIO:
            return RangoEtario.orden
        return self.get_dimension_column(dim_code)

    def build_base_query(self, metric: MetricDefinition):
        """Query base con todos los JOINs necesarios."""
        return (
            select(ConteoCamasIRA)
            .join(
                NotificacionSemanal,
                col(ConteoCamasIRA.notificacion_id) == col(NotificacionSemanal.id),
            )
            .join(
                TipoCasoEpidemiologicoPasivo,
                col(ConteoCamasIRA.tipo_evento_id)
                == col(TipoCasoEpidemiologicoPasivo.id),
            )
            .join(
                RangoEtario,
                col(ConteoCamasIRA.rango_etario_id) == col(RangoEtario.id),
            )
            .outerjoin(
                Establecimiento,
                col(NotificacionSemanal.establecimiento_id) == col(Establecimiento.id),
            )
            .outerjoin(
                Localidad,
                col(Establecimiento.id_localidad_indec)
                == col(Localidad.id_localidad_indec),
            )
            .outerjoin(
                Departamento,
                col(Localidad.id_departamento_indec)
                == col(Departamento.id_departamento_indec),
            )
            .outerjoin(
                Provincia,
                col(Departamento.id_provincia_indec)
                == col(Provincia.id_provincia_indec),
            )
        )

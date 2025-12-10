"""
Query Builders para cada fuente de datos.
=========================================

Cada builder sabe cómo construir queries para su fuente:

- ClinicoQueryBuilder:     ConteoCasosClinicos (CLI_P26)
- LaboratorioQueryBuilder: ConteoEstudiosLab (LAB_P26)
- HospitalarioQueryBuilder: ConteoCamasIRA (CLI_P26_INT)
- NominalQueryBuilder:     CasoEpidemiologico (nominales)

ARQUITECTURA:
    Cada builder hereda de MetricQueryBuilder y debe implementar:

    def build_base_query(self, metric: MetricDefinition):
        '''Retorna query SELECT con todos los JOINs necesarios.'''
        return (
            select(MiModelo)
            .join(OtroModelo, ...)
            ...
        )

Los JOINs necesarios dependen de la fuente:
    - Clínico: NotificacionSemanal, TipoCasoEpidemiologicoPasivo, RangoEtario, geografía
    - Laboratorio: NotificacionSemanal, AgenteEtiologico, RangoEtario, geografía
    - Hospitalario: Similar a clínico
    - Nominal: Enfermedad, Ciudadano, geografía (con Lazy Joins para optimización)

USO:
    builder = ClinicoQueryBuilder(session)
    data = (
        builder
        .with_dimensions(DimensionCode.SEMANA_EPIDEMIOLOGICA)
        .with_criteria(RangoPeriodoCriterion(2025, 1, 2025, 20))
        .order_by_dimensions()
        .execute(metric_def)
    )

NOTA: Normalmente no se usan directamente. MetricService selecciona el builder
apropiado según el MetricSource de la métrica.
"""

from .base import MetricQueryBuilder
from .clinico import ClinicoQueryBuilder
from .hospitalario import HospitalarioQueryBuilder
from .laboratorio import LaboratorioQueryBuilder
from .nominal import NominalQueryBuilder

__all__ = [
    "MetricQueryBuilder",
    "ClinicoQueryBuilder",
    "LaboratorioQueryBuilder",
    "HospitalarioQueryBuilder",
    "NominalQueryBuilder",
]

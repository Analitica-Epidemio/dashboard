"""
Motor de Métricas Epidemiológicas
=================================

Sistema unificado para consultas de métricas usando el patrón Criteria.

ARQUITECTURA
------------

                          ┌─────────────────────┐
                          │   MetricService     │  <- Punto de entrada (Facade)
                          │                     │
                          └──────────┬──────────┘
                                     │
          ┌──────────────────────────┼──────────────────────────┐
          │                          │                          │
          ▼                          ▼                          ▼
    ┌───────────┐            ┌───────────────┐          ┌─────────────┐
    │ Criteria  │            │   Builders    │          │  Registry   │
    │           │            │               │          │             │
    │ Temporal  │            │ ClinicoQB     │          │ Metrics     │
    │ Evento    │            │ LaboratorioQB │          │ Dimensions  │
    │ Geografico│            │ HospitalarioQB│          │             │
    └───────────┘            │ NominalQB     │          └─────────────┘
                             └───────────────┘


PATRÓN CRITERIA (Specification Pattern)
---------------------------------------

El patrón Criteria permite construir filtros de forma composable y type-safe.
Cada criterio encapsula una condición que se traduce a expresión SQLAlchemy.

USO BÁSICO:

    from app.domains.metricas import MetricService
    from app.domains.metricas.criteria import (
        RangoPeriodoCriterion,
        TipoEventoCriterion,
        ProvinciaCriterion,
    )

    service = MetricService(session)

    # Criterios se combinan con & (AND) y | (OR)
    criterio = (
        RangoPeriodoCriterion(2025, 1, 2025, 20)  # SE 1-20 de 2025
        & TipoEventoCriterion(ids=[1, 2])  # IDs de eventos
        & ProvinciaCriterion(ids=[6])  # Chubut
    )

    result = service.query(
        metric="casos_clinicos",
        dimensions=["SEMANA_EPIDEMIOLOGICA", "TIPO_EVENTO"],
        criteria=criterio,
    )


CRITERIOS DISPONIBLES
---------------------

CONVENCIÓN: Los filtros por ID siempre usan listas (ids: list[int]).
Esto simplifica el código y SQL IN(1) es igual de eficiente que = 1.

Temporal:
    - RangoPeriodoCriterion(anio_desde, semana_desde, anio_hasta, semana_hasta)
      Filtra por rango de período epidemiológico. Puede cruzar años.

    - AniosMultiplesCriterion(anios=[2022, 2023, 2024])
      Para corredor endémico: incluye múltiples años.

Evento:
    - TipoEventoCriterion(ids=[1,2], nombre="ETI")
      Filtra por tipo(s) de evento. ids para IDs exactos, nombre para búsqueda fuzzy.

    - AgenteCriterion(ids=[10,20], nombre="Influenza")
      Filtra por agente(s) etiológico (para laboratorio).

    - AgrupacionAgentesCriterion(ids=[1,2])
      Filtra por agrupación(es) de agentes (Influenza A, VSR, etc.)

Geográfico:
    - ProvinciaCriterion(ids=[6], nombre="Chubut")
    - DepartamentoCriterion(ids=[...], nombre="Rawson")
    - EstablecimientoCriterion(ids=[...], nombre="Hospital")


MÉTRICAS DISPONIBLES
--------------------

Ver registry/metrics.py para la lista completa. Principales:

    - casos_clinicos: Conteos de vigilancia clínica (CLI_P26)
    - muestras_estudiadas: Estudios de laboratorio (LAB_P26)
    - muestras_positivas: Positivos por agente
    - tasa_positividad: Derivada (positivas/estudiadas × 100)
    - casos_nominales: Casos individuales
    - ocupacion_camas_ira: Camas hospitalarias (CLI_P26_INT)


DIMENSIONES
-----------

Ver registry/dimensions.py. Las métricas declaran qué dimensiones permiten:

    - SEMANA_EPIDEMIOLOGICA: Semana 1-52/53
    - ANIO_EPIDEMIOLOGICO: Año
    - TIPO_EVENTO: Enfermedad/síndrome
    - AGENTE_ETIOLOGICO: Patógeno (laboratorio)
    - GRUPO_ETARIO: Rango de edad
    - SEXO: M/F/X
    - PROVINCIA, DEPARTAMENTO, ESTABLECIMIENTO


COMPUTACIONES POST-QUERY
------------------------

    result = service.query(
        metric="casos_clinicos",
        dimensions=["SEMANA_EPIDEMIOLOGICA", "ANIO_EPIDEMIOLOGICO"],
        criteria=AniosMultiplesCriterion([2022, 2023, 2024, 2025]),
        compute="corredor_endemico",  # Calcula percentiles
    )

    # Retorna:
    # {
    #     "semana_epidemiologica": 1,
    #     "valor_actual": 150,       # Casos del año actual
    #     "zona_exito": 80,          # p25
    #     "zona_seguridad": 100,     # p50
    #     "zona_alerta": 130,        # p75
    #     "zona_brote": 160,         # p90
    # }
"""

from .registry.dimensions import DimensionCode, get_dimension
from .registry.metrics import MetricSource, get_metric, list_metrics
from .service import MetricService

__all__ = [
    # Servicio principal
    "MetricService",
    # Enums y helpers
    "MetricSource",
    "DimensionCode",
    "get_metric",
    "list_metrics",
    "get_dimension",
]

"""
Criterios para filtrado de métricas (Specification Pattern).
============================================================

Los criterios encapsulan condiciones de filtro que se traducen a expresiones
SQLAlchemy. Se pueden combinar con operadores & (AND) y | (OR).

EJEMPLO:
    from app.domains.metricas.criteria import (
        RangoPeriodoCriterion,
        TipoEventoCriterion,
        ProvinciaCriterion,
    )

    # Criterio compuesto
    criterio = (
        RangoPeriodoCriterion(2025, 1, 2025, 20)
        & TipoEventoCriterion(evento_nombre="ETI")
        & ProvinciaCriterion(provincia_id=6)
    )

    # Usar con MetricService
    result = service.query(
        metric="casos_clinicos",
        dimensions=["SEMANA_EPIDEMIOLOGICA"],
        criteria=criterio,
    )

CÓMO FUNCIONA:
    1. Cada criterio es un dataclass con parámetros opcionales
    2. to_expression() traduce a SQLAlchemy BinaryExpression
    3. __and__ y __or__ permiten combinar criterios
    4. Los builders aplican las expresiones a sus queries

CREAR UN NUEVO CRITERIO:
    @dataclass
    class MiCriterion(Criterion):
        mi_campo: Optional[int] = None

        def to_expression(self) -> BinaryExpression | None:
            if self.mi_campo:
                return MiModelo.campo == self.mi_campo
            return None  # No filtra si no hay valor
"""

# Base
from .base import (
    AndCriteria,
    Criterion,
    EmptyCriterion,
    OrCriteria,
)

# Evento
from .evento import (
    AgenteCriterion,
    AgrupacionAgentesCriterion,
    TipoEventoCriterion,
)

# Geográficos
from .geografico import (
    DepartamentoCriterion,
    EstablecimientoCriterion,
    ProvinciaCriterion,
)

# Temporales
from .temporal import (
    AniosMultiplesCriterion,
    RangoPeriodoCriterion,
)

__all__ = [
    # Base
    "Criterion",
    "AndCriteria",
    "OrCriteria",
    "EmptyCriterion",
    # Temporales
    "RangoPeriodoCriterion",
    "AniosMultiplesCriterion",
    # Evento
    "TipoEventoCriterion",
    "AgenteCriterion",
    "AgrupacionAgentesCriterion",
    # Geográficos
    "ProvinciaCriterion",
    "DepartamentoCriterion",
    "EstablecimientoCriterion",
]

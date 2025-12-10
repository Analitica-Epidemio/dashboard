"""
Criterios temporales para filtros de métricas.

Filtros por semana epidemiológica, año, rangos de fechas.
"""

from dataclasses import dataclass

from sqlalchemy import BinaryExpression, and_, or_
from sqlmodel import col

from app.domains.vigilancia_agregada.models.cargas import NotificacionSemanal

from .base import Criterion


@dataclass
class RangoPeriodoCriterion(Criterion):
    """
    Filtra por rango de período que puede cruzar años.

    Este es el criterio temporal principal. Puede expresar:
    - Semana exacta: RangoPeriodoCriterion(2025, 5, 2025, 5)
    - Rango en un año: RangoPeriodoCriterion(2025, 1, 2025, 10)
    - Rango multi-año: RangoPeriodoCriterion(2024, 40, 2025, 20)

    Ejemplos:
    - SE 1-20/2025: mismo año
    - SE 40/2024 - SE 20/2025: cruza años

    La query generada maneja ambos casos eficientemente.
    """

    anio_desde: int
    semana_desde: int
    anio_hasta: int
    semana_hasta: int

    def to_expression(self) -> BinaryExpression:  # type: ignore[return-value]
        if self.anio_desde == self.anio_hasta:
            # Mismo año - query simple y eficiente
            return and_(  # type: ignore[return-value]
                col(NotificacionSemanal.anio) == self.anio_desde,
                col(NotificacionSemanal.semana) >= self.semana_desde,
                col(NotificacionSemanal.semana) <= self.semana_hasta,
            )

        # Cruzando años - necesitamos OR de tres condiciones:
        # 1. (anio = inicio AND semana >= desde)
        # 2. (anio > inicio AND anio < fin) - años completos intermedios
        # 3. (anio = fin AND semana <= hasta)

        conditions = [
            # Primer año parcial
            and_(
                col(NotificacionSemanal.anio) == self.anio_desde,
                col(NotificacionSemanal.semana) >= self.semana_desde,
            ),
            # Último año parcial
            and_(
                col(NotificacionSemanal.anio) == self.anio_hasta,
                col(NotificacionSemanal.semana) <= self.semana_hasta,
            ),
        ]

        # Años intermedios completos (si los hay)
        if self.anio_hasta - self.anio_desde > 1:
            conditions.append(
                and_(
                    col(NotificacionSemanal.anio) > self.anio_desde,
                    col(NotificacionSemanal.anio) < self.anio_hasta,
                )
            )

        return or_(*conditions)  # type: ignore[return-value]


@dataclass
class AniosMultiplesCriterion(Criterion):
    """
    Filtra para incluir múltiples años (para corredor endémico).

    Útil cuando se necesitan años no consecutivos o para calcular
    percentiles históricos.

    Ejemplo:
        AniosMultiplesCriterion([2020, 2021, 2022, 2023, 2024])
    """

    anios: list[int]

    def to_expression(self) -> BinaryExpression:  # type: ignore[return-value]
        return col(NotificacionSemanal.anio).in_(self.anios)  # type: ignore[return-value]

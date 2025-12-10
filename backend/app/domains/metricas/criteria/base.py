"""
Patrón Criteria para filtros type-safe y componibles.

Los criterios se pueden combinar con & (AND) y | (OR).
"""

from abc import ABC, abstractmethod

from sqlalchemy import BinaryExpression, and_, or_


class Criterion(ABC):
    """Criterio base abstracto."""

    @abstractmethod
    def to_expression(self) -> BinaryExpression | None:
        """Convierte el criterio a expresión SQLAlchemy."""
        pass

    def __and__(self, other: "Criterion") -> "AndCriteria":
        """Permite combinar criterios con &."""
        return AndCriteria(self, other)

    def __or__(self, other: "Criterion") -> "OrCriteria":
        """Permite combinar criterios con |."""
        return OrCriteria(self, other)


class AndCriteria(Criterion):
    """Combina criterios con AND."""

    def __init__(self, *criteria: Criterion):
        self.criteria = criteria

    def to_expression(self) -> BinaryExpression | None:
        expressions = [
            c.to_expression() for c in self.criteria if c.to_expression() is not None
        ]
        return and_(*expressions) if expressions else None  # type: ignore[return-value]


class OrCriteria(Criterion):
    """Combina criterios con OR."""

    def __init__(self, *criteria: Criterion):
        self.criteria = criteria

    def to_expression(self) -> BinaryExpression | None:
        expressions = [
            c.to_expression() for c in self.criteria if c.to_expression() is not None
        ]
        return or_(*expressions) if expressions else None  # type: ignore[return-value]


class EmptyCriterion(Criterion):
    """Criterio vacío (no aplica ningún filtro)."""

    def to_expression(self) -> None:
        return None

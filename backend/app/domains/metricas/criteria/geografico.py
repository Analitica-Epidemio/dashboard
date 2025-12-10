"""
Criterios geográficos para filtros de métricas.

Filtros por provincia, departamento, establecimiento.

CONVENCIÓN: Los filtros por ID siempre usan listas.
"""

from dataclasses import dataclass

from sqlalchemy import BinaryExpression
from sqlmodel import col

from app.domains.territorio.establecimientos_models import Establecimiento
from app.domains.territorio.geografia_models import Departamento, Provincia

from .base import Criterion


@dataclass
class ProvinciaCriterion(Criterion):
    """
    Filtra por provincia(s).

    Uso:
        ProvinciaCriterion(ids=[6])  # Chubut
        ProvinciaCriterion(nombre="Chubut")  # búsqueda fuzzy
    """

    ids: list[int] | None = None
    nombre: str | None = None

    def to_expression(self) -> BinaryExpression | None:
        if self.ids:
            return col(Provincia.id).in_(self.ids)
        elif self.nombre:
            return col(Provincia.nombre).ilike(f"%{self.nombre}%")
        return None


@dataclass
class DepartamentoCriterion(Criterion):
    """
    Filtra por departamento(s).

    Uso:
        DepartamentoCriterion(ids=[1, 2, 3])
        DepartamentoCriterion(nombre="Rawson")  # búsqueda fuzzy
    """

    ids: list[int] | None = None
    nombre: str | None = None

    def to_expression(self) -> BinaryExpression | None:
        if self.ids:
            return col(Departamento.id).in_(self.ids)
        elif self.nombre:
            return col(Departamento.nombre).ilike(f"%{self.nombre}%")
        return None


@dataclass
class EstablecimientoCriterion(Criterion):
    """
    Filtra por establecimiento(s).

    Uso:
        EstablecimientoCriterion(ids=[100, 200])
        EstablecimientoCriterion(nombre="Hospital")  # búsqueda fuzzy
    """

    ids: list[int] | None = None
    nombre: str | None = None

    def to_expression(self) -> BinaryExpression | None:
        if self.ids:
            return col(Establecimiento.id).in_(self.ids)
        elif self.nombre:
            return col(Establecimiento.nombre).ilike(f"%{self.nombre}%")
        return None

"""
Criterios de evento para filtros de métricas.

Filtros por tipo de evento, agente etiológico, agrupación de agentes.

CONVENCIÓN: Los filtros por ID siempre usan listas (evento_ids, agente_ids).
Esto simplifica el código (un solo path) y SQL IN(1) = SQL = 1 en performance.
"""

from dataclasses import dataclass

from sqlalchemy import BinaryExpression
from sqlmodel import col

from app.domains.catalogos.agentes.agrupacion import AgrupacionAgentes
from app.domains.catalogos.agentes.models import AgenteEtiologico
from app.domains.vigilancia_agregada.models.catalogos import (
    TipoCasoEpidemiologicoPasivo,
)

from .base import Criterion


@dataclass
class TipoEventoCriterion(Criterion):
    """
    Filtra por tipo(s) de evento de vigilancia pasiva.

    Uso:
        TipoEventoCriterion(ids=[1, 2, 3])
        TipoEventoCriterion(nombre="ETI")  # búsqueda fuzzy
        TipoEventoCriterion(slug="eti")  # exacto por slug
    """

    ids: list[int] | None = None
    nombre: str | None = None
    slug: str | None = None

    def to_expression(self) -> BinaryExpression | None:
        if self.ids:
            return col(TipoCasoEpidemiologicoPasivo.id).in_(self.ids)
        elif self.slug:
            return col(TipoCasoEpidemiologicoPasivo.slug) == self.slug
        elif self.nombre:
            return col(TipoCasoEpidemiologicoPasivo.nombre).ilike(f"%{self.nombre}%")
        return None


@dataclass
class AgenteCriterion(Criterion):
    """
    Filtra por agente(s) etiológico (para laboratorio).

    Uso:
        AgenteCriterion(ids=[10, 20])
        AgenteCriterion(nombre="Influenza")  # búsqueda fuzzy
    """

    ids: list[int] | None = None
    nombre: str | None = None

    def to_expression(self) -> BinaryExpression | None:
        if self.ids:
            return col(AgenteEtiologico.id).in_(self.ids)
        elif self.nombre:
            return col(AgenteEtiologico.nombre).ilike(f"%{self.nombre}%")
        return None


@dataclass
class AgrupacionAgentesCriterion(Criterion):
    """
    Filtra por agrupación de agentes (para boletines).

    La agrupación agrupa múltiples agentes individuales bajo una etiqueta
    visual (ej: "Influenza A" agrupa variantes H1N1, H3N2, etc.).

    Uso:
        AgrupacionAgentesCriterion(ids=[1, 2])
        AgrupacionAgentesCriterion(slug="influenza-a")  # exacto por slug
    """

    ids: list[int] | None = None
    slug: str | None = None

    def to_expression(self) -> BinaryExpression | None:
        if self.ids:
            return col(AgrupacionAgentes.id).in_(self.ids)
        elif self.slug:
            return col(AgrupacionAgentes.slug) == self.slug
        return None

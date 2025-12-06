"""
Query builders and criteria patterns for consistent database queries.

This module provides reusable query builders that ensure consistency
across different endpoints that query the same domain entities.
"""

from app.domains.vigilancia_nominal.queries.evento_filters import CasoEpidemiologicoQueryBuilder

__all__ = ["CasoEpidemiologicoQueryBuilder"]

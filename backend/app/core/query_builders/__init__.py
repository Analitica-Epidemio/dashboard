"""
Query builders and criteria patterns for consistent database queries.

This module provides reusable query builders that ensure consistency
across different endpoints that query the same domain entities.
"""

from app.core.query_builders.evento_filters import EventoQueryBuilder

__all__ = ["EventoQueryBuilder"]

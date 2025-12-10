"""Definiciones de columnas para procesadores de vigilancia agregada."""

from .base import ColumnDefinition, ColumnRegistry, ColumnType
from .cli_p26 import CLI_P26_COLUMNS
from .cli_p26_int import CLI_P26_INT_COLUMNS
from .lab_p26 import LAB_P26_COLUMNS

__all__ = [
    "ColumnDefinition",
    "ColumnRegistry",
    "ColumnType",
    "CLI_P26_COLUMNS",
    "CLI_P26_INT_COLUMNS",
    "LAB_P26_COLUMNS",
]

"""Configuration for file processing."""

from .columns import Columns
from .constants import (
    BATCH_SIZES,
    BOOLEAN_MAPPING,
    DATE_COLUMNS_LIST,
    DOCUMENTO_MAPPING,
    NUMERIC_COLUMNS_LIST,
    SEXO_MAPPING,
    ProcessingStage,
    ProcessingStatus,
)
from .context import ProcessingContext

__all__ = [
    "BATCH_SIZES",
    "BOOLEAN_MAPPING",
    "DATE_COLUMNS_LIST",
    "DOCUMENTO_MAPPING",
    "NUMERIC_COLUMNS_LIST",
    "SEXO_MAPPING",
    "Columns",
    "ProcessingContext",
    "ProcessingStage",
    "ProcessingStatus",
]

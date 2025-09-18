"""
Core components for epidemiological file processing.

Provides the foundation classes and utilities for the new architecture.
"""

from .base_processor import (
    BaseProcessor,
    BatchProcessor,
    ProcessingContext,
    ProcessingStats,
)
from .columns import Columns
from .constants import (
    BATCH_SIZES,
    ProcessingStage,
    ProcessingStatus,
)

__all__ = [
    # Column system
    "Columns",
    # Base classes
    "BaseProcessor",
    "BatchProcessor",
    "ProcessingContext",
    "ProcessingStats",
    # Constants
    "ProcessingStage",
    "ProcessingStatus",
    "BATCH_SIZES",
]

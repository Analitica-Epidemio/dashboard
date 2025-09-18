"""Result dataclass for bulk operations."""

from dataclasses import dataclass
from typing import List


@dataclass
class BulkOperationResult:
    """Resultado de operación bulk con métricas."""
    
    inserted_count: int
    updated_count: int
    skipped_count: int
    errors: List[str]
    duration_seconds: float
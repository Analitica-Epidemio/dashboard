"""Procesadores por tipo de archivo."""

from .base_type import FileTypeProcessor
from .cli_p26 import CLIP26Processor
from .cli_p26_int import CLIP26IntProcessor
from .lab_p26 import LabP26Processor

__all__ = [
    "FileTypeProcessor",
    "CLIP26Processor",
    "CLIP26IntProcessor",
    "LabP26Processor",
]

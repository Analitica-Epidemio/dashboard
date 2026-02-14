"""
Base definitions for column handling.

Provides ColumnDefinition dataclass and ColumnRegistry for validation.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import polars as pl


class ColumnType(str, Enum):
    """Tipos de columna soportados."""

    INTEGER = "integer"
    STRING = "string"
    DATETIME = "datetime"
    FLOAT = "float"
    BOOLEAN = "boolean"


@dataclass
class ColumnDefinition:
    """
    Definición de una columna de archivo.

    Attributes:
        source_name: Nombre en el archivo fuente
        target_name: Nombre normalizado para procesamiento interno
        col_type: Tipo de dato
        required: Si es obligatoria
        nullable: Si permite nulos
        transform: Función de transformación opcional
        default: Valor por defecto si falta
    """

    source_name: str
    target_name: str
    col_type: ColumnType
    required: bool = True
    nullable: bool = True
    transform: Callable[[Any], Any] | None = None
    default: Any = None

    def apply_transform(self, value: Any) -> Any:
        """Aplica transformación si existe."""
        if value is None and self.default is not None:
            return self.default
        if self.transform and value is not None:
            return self.transform(value)
        return value


@dataclass
class ColumnRegistry:
    """
    Registro de columnas para un tipo de archivo.

    Permite validar y transformar DataFrames.
    """

    columns: list[ColumnDefinition] = field(default_factory=list)
    file_type: str = ""

    @property
    def source_names(self) -> list[str]:
        """Lista de nombres de columnas en archivo fuente."""
        return [c.source_name for c in self.columns]

    @property
    def required_columns(self) -> list[str]:
        """Lista de columnas obligatorias."""
        return [c.source_name for c in self.columns if c.required]

    @property
    def source_to_target_map(self) -> dict[str, str]:
        """Mapeo de nombres fuente a nombres internos."""
        return {c.source_name: c.target_name for c in self.columns}

    def validate(self, df: pl.DataFrame) -> tuple[bool, list[str]]:
        """
        Valida que el DataFrame tenga las columnas requeridas.

        Returns:
            (is_valid, missing_columns)
        """
        missing = [col for col in self.required_columns if col not in df.columns]

        return len(missing) == 0, missing

    def get_column_by_source(self, source_name: str) -> ColumnDefinition | None:
        """Obtiene definición de columna por nombre fuente."""
        for col in self.columns:
            if col.source_name == source_name:
                return col
        return None

    def rename_columns(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Renombra columnas del DataFrame según el mapeo.

        Solo renombra las columnas que existen en el DataFrame.
        """
        rename_map = {}
        for col in self.columns:
            if col.source_name in df.columns:
                rename_map[col.source_name] = col.target_name

        return df.rename(rename_map)

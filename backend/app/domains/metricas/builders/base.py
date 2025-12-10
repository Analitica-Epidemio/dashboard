"""
Builder base abstracto para queries de métricas.

Define la interfaz común que todos los builders deben implementar.
Cada builder DEBE implementar get_dimension_column() con su propio mapeo.
"""

from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from app.domains.metricas.criteria.base import Criterion
from app.domains.metricas.registry.dimensions import (
    DIMENSIONS,
    DimensionCode,
    DimensionDefinition,
)
from app.domains.metricas.registry.metrics import MetricDefinition


class MetricQueryBuilder(ABC):
    """
    Builder abstracto para queries de métricas.

    Cada source (clínico, lab, nominal) implementa su propio builder
    que sabe cómo hacer los JOINs necesarios y mapear dimensiones a columnas.

    IMPORTANTE: Cada builder DEBE implementar:
    - build_base_query(): Query base con JOINs
    - get_dimension_column(): Mapeo de DimensionCode a columna SQL

    Uso:
        builder = ClinicoQueryBuilder(session)
        result = (
            builder
            .with_dimensions(DimensionCode.SEMANA_EPIDEMIOLOGICA, DimensionCode.TIPO_EVENTO)
            .with_criteria(RangoPeriodoCriterion(2025, 1, 2025, 10))
            .order_by_dimensions()
            .execute(metric_def)
        )
    """

    def __init__(self, session: Session):
        self.session = session
        self._dimensions: list[DimensionDefinition] = []
        self._criteria: Criterion | None = None
        self._order_by_dims: bool = False

    @abstractmethod
    def build_base_query(self, metric: MetricDefinition):
        """
        Retorna la query base con todos los JOINs necesarios.

        Cada builder implementa esto según su source de datos.
        """
        pass

    @abstractmethod
    def get_dimension_column(self, dim_code: DimensionCode):
        """
        Mapea un DimensionCode a la columna SQL correspondiente.

        CADA BUILDER DEBE IMPLEMENTAR ESTO - no hay fallback.

        Ejemplo:
            def get_dimension_column(self, dim_code: DimensionCode):
                return {
                    DimensionCode.SEMANA_EPIDEMIOLOGICA: NotificacionSemanal.semana,
                    DimensionCode.TIPO_EVENTO: TipoCasoEpidemiologicoPasivo.nombre,
                    ...
                }[dim_code]
        """
        pass

    def get_dimension_order_column(self, dim_code: DimensionCode):
        """
        Columna para ORDER BY (por defecto, igual que la columna de dimensión).

        Sobrescribir si necesitas orden diferente (ej: GRUPO_ETARIO usa RangoEtario.orden).
        """
        return self.get_dimension_column(dim_code)

    def with_dimensions(self, *dimensions: DimensionCode) -> "MetricQueryBuilder":
        """
        Agrega dimensiones para agrupar.

        Args:
            dimensions: Códigos de dimensión (SEMANA_EPIDEMIOLOGICA, TIPO_EVENTO, etc.)
        """
        for dim_code in dimensions:
            if dim_code in DIMENSIONS:
                self._dimensions.append(DIMENSIONS[dim_code])
        return self

    def with_criteria(self, criteria: Criterion) -> "MetricQueryBuilder":
        """
        Agrega criterios de filtro.

        Los criterios se pueden combinar: RangoPeriodoCriterion(...) & TipoEventoCriterion(...)
        """
        self._criteria = criteria
        return self

    def order_by_dimensions(self) -> "MetricQueryBuilder":
        """Ordena por las dimensiones agregadas."""
        self._order_by_dims = True
        return self

    def execute(self, metric: MetricDefinition) -> list[dict]:
        """
        Ejecuta la query y retorna resultados.

        Returns:
            Lista de diccionarios con los resultados.
            Cada dict tiene las dimensiones como claves + "valor" para la métrica.
        """
        # 1. Obtener query base con JOINs
        query = self.build_base_query(metric)

        # 2. Construir columnas de SELECT
        select_columns = []
        group_by_columns = []

        # Agregar dimensiones
        order_columns = []
        for dim in self._dimensions:
            col = self.get_dimension_column(dim.code)
            select_columns.append(col.label(dim.code.value.lower()))
            group_by_columns.append(col)
            # Si hay columna de orden diferente, incluirla en GROUP BY
            order_col = self.get_dimension_order_column(dim.code)
            if order_col is not col:
                group_by_columns.append(order_col)
            order_columns.append(order_col)

        # Agregar agregación de la métrica
        agg_expr = metric.get_aggregation_expr()
        if agg_expr is not None:
            select_columns.append(agg_expr.label("valor"))

        # 3. Modificar query con SELECT explícito
        if select_columns:
            query = query.with_only_columns(*select_columns)

        # 4. Aplicar criterios
        if self._criteria:
            expr = self._criteria.to_expression()
            if expr is not None:
                query = query.where(expr)

        # 5. Aplicar GROUP BY
        if group_by_columns:
            query = query.group_by(*group_by_columns)

        # 6. Aplicar ORDER BY
        if self._order_by_dims and order_columns:
            for order_col in order_columns:
                query = query.order_by(order_col)

        # 7. Ejecutar
        result = self.session.execute(query)
        return [dict(row._mapping) for row in result]

    def reset(self) -> "MetricQueryBuilder":
        """Resetea el builder para reutilizar."""
        self._dimensions = []
        self._criteria = None
        self._order_by_dims = False
        return self

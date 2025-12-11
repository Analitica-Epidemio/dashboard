"""
Builder para métricas de vigilancia nominal.

Construye queries sobre CasoEpidemiologico con los JOINs necesarios.
"""

from sqlalchemy import and_, case, func
from sqlmodel import col, select

from app.domains.metricas.criteria.base import AndCriteria, Criterion, OrCriteria
from app.domains.metricas.criteria.geografico import (
    DepartamentoCriterion,
    EstablecimientoCriterion,
    ProvinciaCriterion,
)
from app.domains.metricas.criteria.temporal import (
    AniosMultiplesCriterion,
    RangoPeriodoCriterion,
)
from app.domains.metricas.registry.dimensions import DimensionCode
from app.domains.metricas.registry.metrics import MetricDefinition
from app.domains.territorio.establecimientos_models import Establecimiento
from app.domains.territorio.geografia_models import (
    Departamento,
    Domicilio,
    Localidad,
    Provincia,
)
from app.domains.vigilancia_nominal.models.caso import CasoEpidemiologico
from app.domains.vigilancia_nominal.models.enfermedad import Enfermedad
from app.domains.vigilancia_nominal.models.sujetos import Ciudadano

from .base import MetricQueryBuilder


def _build_age_group_expression():
    """Expresión SQL CASE para calcular grupo etario."""
    age_in_years = func.extract(
        "year",
        func.age(
            CasoEpidemiologico.fecha_minima_caso, CasoEpidemiologico.fecha_nacimiento
        ),
    )
    return case(
        (col(CasoEpidemiologico.fecha_nacimiento).is_(None), "Sin dato"),
        (age_in_years < 1, "< 1 año"),
        (age_in_years < 5, "1-4 años"),
        (age_in_years < 10, "5-9 años"),
        (age_in_years < 15, "10-14 años"),
        (age_in_years < 25, "15-24 años"),
        (age_in_years < 35, "25-34 años"),
        (age_in_years < 45, "35-44 años"),
        (age_in_years < 55, "45-54 años"),
        (age_in_years < 65, "55-64 años"),
        else_="65+ años",
    )


def _build_age_group_order_expression():
    """Expresión para ordenar los grupos etarios."""
    age_in_years = func.extract(
        "year",
        func.age(
            CasoEpidemiologico.fecha_minima_caso, CasoEpidemiologico.fecha_nacimiento
        ),
    )
    return case(
        (col(CasoEpidemiologico.fecha_nacimiento).is_(None), 999),
        (age_in_years < 1, 1),
        (age_in_years < 5, 2),
        (age_in_years < 10, 3),
        (age_in_years < 15, 4),
        (age_in_years < 25, 5),
        (age_in_years < 35, 6),
        (age_in_years < 45, 7),
        (age_in_years < 55, 8),
        (age_in_years < 65, 9),
        else_=10,
    )


class NominalQueryBuilder(MetricQueryBuilder):
    """
    Builder para queries sobre CasoEpidemiologico.

    Incluye JOINs necesarios para:
    - Enfermedad (tipo de evento)
    - Domicilio -> Localidad -> Departamento -> Provincia (geografía)
    - Establecimiento (si se filtra)

    Nota: Implementa Lazy Joins para optimizar performance.
    """

    def get_dimension_column(self, dim_code: DimensionCode):
        """Mapeo de dimensiones a columnas SQL."""
        if dim_code == DimensionCode.GRUPO_ETARIO:
            return _build_age_group_expression()
        return {
            DimensionCode.SEMANA_EPIDEMIOLOGICA: CasoEpidemiologico.fecha_minima_caso_semana_epi,
            DimensionCode.ANIO_EPIDEMIOLOGICO: CasoEpidemiologico.fecha_minima_caso_anio_epi,
            DimensionCode.TIPO_EVENTO: Enfermedad.nombre,
            DimensionCode.SEXO: Ciudadano.sexo_biologico,
            DimensionCode.PROVINCIA: Provincia.nombre,
            DimensionCode.DEPARTAMENTO: Departamento.nombre,
        }[dim_code]

    def get_dimension_order_column(self, dim_code: DimensionCode):
        """Columna de orden (GRUPO_ETARIO usa expresión especial)."""
        if dim_code == DimensionCode.GRUPO_ETARIO:
            return _build_age_group_order_expression()
        return self.get_dimension_column(dim_code)

    def _analyze_dependencies(self) -> dict:
        """Analiza dimensiones y criterios para determinar qué tablas necesitan JOIN."""
        deps = {
            "enfermedad": False,
            "geo_level": 0,  # 0: None, 1: Domicilio, 2: Localidad, 3: Depto, 4: Prov
            "establecimiento": False,
            "ciudadano": False,
        }

        for dim in self._dimensions:
            if dim.code == DimensionCode.TIPO_EVENTO:
                deps["enfermedad"] = True
            elif dim.code == DimensionCode.PROVINCIA:
                deps["geo_level"] = max(deps["geo_level"], 4)
            elif dim.code == DimensionCode.DEPARTAMENTO:
                deps["geo_level"] = max(deps["geo_level"], 3)
            elif dim.code == DimensionCode.SEXO:
                deps["ciudadano"] = True

        if self._criteria:
            self._check_criteria_recursive(self._criteria, deps)

        return deps

    def _check_criteria_recursive(self, criterion: Criterion, deps: dict):
        """Recorre recursivamente los criterios para detectar dependencias."""
        if isinstance(criterion, (AndCriteria, OrCriteria)):
            for c in criterion.criteria:
                self._check_criteria_recursive(c, deps)
        elif isinstance(criterion, ProvinciaCriterion):
            deps["geo_level"] = max(deps["geo_level"], 4)
        elif isinstance(criterion, DepartamentoCriterion):
            deps["geo_level"] = max(deps["geo_level"], 3)
        elif isinstance(criterion, EstablecimientoCriterion):
            deps["establecimiento"] = True

    def build_base_query(self, metric: MetricDefinition):
        """Query base con JOINs condicionales (Lazy Joins)."""
        deps = self._analyze_dependencies()
        query = select(CasoEpidemiologico)

        if deps["enfermedad"]:
            query = query.join(
                Enfermedad,
                col(CasoEpidemiologico.id_enfermedad) == col(Enfermedad.id),
            )

        if deps["ciudadano"]:
            query = query.outerjoin(
                Ciudadano,
                col(CasoEpidemiologico.codigo_ciudadano)
                == col(Ciudadano.codigo_ciudadano),
            )

        if deps["geo_level"] >= 1:
            query = query.outerjoin(
                Domicilio,
                col(CasoEpidemiologico.id_domicilio) == col(Domicilio.id),
            )
        if deps["geo_level"] >= 2:
            query = query.outerjoin(
                Localidad,
                col(Domicilio.id_localidad_indec) == col(Localidad.id_localidad_indec),
            )
        if deps["geo_level"] >= 3:
            query = query.outerjoin(
                Departamento,
                col(Localidad.id_departamento_indec)
                == col(Departamento.id_departamento_indec),
            )
        if deps["geo_level"] >= 4:
            query = query.outerjoin(
                Provincia,
                col(Departamento.id_provincia_indec)
                == col(Provincia.id_provincia_indec),
            )

        if deps["establecimiento"]:
            query = query.outerjoin(
                Establecimiento,
                col(CasoEpidemiologico.id_establecimiento_notificacion)
                == col(Establecimiento.id),
            )

        return query

    def _transform_criterion_expression(self, criterion: Criterion):
        """Traduce criterios temporales a columnas de CasoEpidemiologico."""
        from sqlalchemy import or_

        if isinstance(criterion, (AndCriteria, OrCriteria)):
            exprs = [
                self._transform_criterion_expression(c) for c in criterion.criteria
            ]
            exprs = [e for e in exprs if e is not None]
            if not exprs:
                return None
            op = and_ if isinstance(criterion, AndCriteria) else or_
            return op(*exprs)

        if isinstance(criterion, RangoPeriodoCriterion):
            if criterion.anio_desde == criterion.anio_hasta:
                return and_(
                    col(CasoEpidemiologico.fecha_minima_caso_anio_epi)
                    == criterion.anio_desde,
                    col(CasoEpidemiologico.fecha_minima_caso_semana_epi)
                    >= criterion.semana_desde,
                    col(CasoEpidemiologico.fecha_minima_caso_semana_epi)
                    <= criterion.semana_hasta,
                )
            conditions = [
                and_(
                    col(CasoEpidemiologico.fecha_minima_caso_anio_epi)
                    == criterion.anio_desde,
                    col(CasoEpidemiologico.fecha_minima_caso_semana_epi)
                    >= criterion.semana_desde,
                ),
                and_(
                    col(CasoEpidemiologico.fecha_minima_caso_anio_epi)
                    == criterion.anio_hasta,
                    col(CasoEpidemiologico.fecha_minima_caso_semana_epi)
                    <= criterion.semana_hasta,
                ),
            ]
            if criterion.anio_hasta - criterion.anio_desde > 1:
                conditions.append(
                    and_(
                        col(CasoEpidemiologico.fecha_minima_caso_anio_epi)
                        > criterion.anio_desde,
                        col(CasoEpidemiologico.fecha_minima_caso_anio_epi)
                        < criterion.anio_hasta,
                    )
                )
            return or_(*conditions)

        if isinstance(criterion, AniosMultiplesCriterion):
            return col(CasoEpidemiologico.fecha_minima_caso_anio_epi).in_(
                criterion.anios
            )

        return criterion.to_expression()

    def execute(self, metric: MetricDefinition) -> list[dict]:
        """Sobrescribe execute para usar _transform_criterion_expression."""
        query = self.build_base_query(metric)

        select_columns = []
        group_by_columns = []
        order_columns = []

        for dim in self._dimensions:
            col = self.get_dimension_column(dim.code)
            select_columns.append(col.label(dim.code.value.lower()))
            group_by_columns.append(col)

            order_col = self.get_dimension_order_column(dim.code)
            if dim.code == DimensionCode.GRUPO_ETARIO or str(order_col) != str(col):
                group_by_columns.append(order_col)
            order_columns.append(order_col)

        agg_expr = metric.get_aggregation_expr()
        if agg_expr is not None:
            select_columns.append(agg_expr.label("valor"))

        if select_columns:
            query = query.with_only_columns(*select_columns)

        if self._criteria:
            expr = self._transform_criterion_expression(self._criteria)
            if expr is not None:
                query = query.where(expr)

        if group_by_columns:
            query = query.group_by(*group_by_columns)

        if self._order_by_dims and order_columns:
            for order_col in order_columns:
                query = query.order_by(order_col)

        result = self.session.execute(query)
        return [dict(row._mapping) for row in result]

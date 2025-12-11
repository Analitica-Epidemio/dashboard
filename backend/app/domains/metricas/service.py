"""
Servicio unificado para consultas de métricas.

Este es el punto de entrada principal (Facade) que expone
todas las capacidades del Metric Engine.
"""

from sqlalchemy.orm import Session

from .builders.clinico import ClinicoQueryBuilder
from .builders.hospitalario import HospitalarioQueryBuilder
from .builders.laboratorio import LaboratorioQueryBuilder
from .builders.nominal import NominalQueryBuilder
from .criteria.base import Criterion
from .registry.dimensions import (
    DIMENSIONS,
    DimensionCode,
)
from .registry.metrics import (
    MetricDefinition,
    MetricSource,
    get_metric,
    list_metrics,
)


class MetricService:
    """
    Servicio unificado para consultas de métricas.

    Uso típico:

        service = MetricService(session)

        # Query simple
        result = service.query(
            metric="casos_clinicos",
            dimensions=["SEMANA_EPIDEMIOLOGICA"],
            criteria=RangoPeriodoCriterion(2025, 1, 2025, 20) & TipoEventoCriterion(evento_nombre="ETI")
        )

        # Listar métricas disponibles
        metrics = service.list_available_metrics()

        # Para el boletín (corredor endémico - a implementar)
        corredor = service.get_corredor_endemico(
            evento_id=123,
            anio=2025,
            anios_base=[2018, 2019, 2022, 2023, 2024]
        )
    """

    def __init__(self, session: Session):
        self.session = session

        # Mapeo de source a builder
        self._builders = {
            MetricSource.CLINICO: ClinicoQueryBuilder,
            MetricSource.LABORATORIO: LaboratorioQueryBuilder,
            MetricSource.HOSPITALARIO: HospitalarioQueryBuilder,
            MetricSource.NOMINAL: NominalQueryBuilder,
        }

    def list_available_metrics(self) -> list[dict]:
        """Retorna métricas disponibles para el frontend."""
        return list_metrics()

    def list_available_dimensions(self) -> list[dict]:
        """Retorna dimensiones disponibles para el frontend."""
        return [
            {
                "code": d.code.value,
                "label": d.label,
                "description": d.description,
            }
            for d in DIMENSIONS.values()
        ]

    def query(
        self,
        metric: str,
        dimensions: list[str] | None = None,
        criteria: Criterion | None = None,
        compute: str | None = None,
        filters: dict | None = None,  # Raw filters from request
    ) -> dict:
        """
        Ejecuta query de métrica.

        Args:
            metric: Código de la métrica (ej: "casos_clinicos")
            dimensions: Lista de códigos de dimensión (ej: ["SEMANA_EPIDEMIOLOGICA"])
            criteria: Criterio de filtro (ej: RangoPeriodoCriterion(2025, 1, 2025, 10))
            compute: Cálculo post-query opcional:
                - "corredor_endemico": Calcula percentiles por semana

        Returns:
            {
                "data": [...],
                "metadata": {...}
            }
        """
        # Validar métrica
        metric_def = get_metric(metric)

        # Parsear dimensiones
        dimension_codes = []
        for dim_str in dimensions or []:
            dim_code = DimensionCode(dim_str)
            if dim_code not in metric_def.allowed_dimensions:
                raise ValueError(
                    f"Dimensión {dim_str} no permitida para métrica {metric}. "
                    f"Permitidas: {[d.value for d in metric_def.allowed_dimensions]}"
                )
            dimension_codes.append(dim_code)

        # Obtener builder para el source
        BuilderClass = self._builders.get(metric_def.source)
        if not BuilderClass:
            raise ValueError(
                f"No hay builder implementado para source: {metric_def.source}"
            )

        # Construir y ejecutar query
        builder = BuilderClass(self.session)
        builder.with_dimensions(*dimension_codes)

        if criteria:
            builder.with_criteria(criteria)

        builder.order_by_dimensions()

        data = builder.execute(metric_def)

        # Post-procesar métricas derivadas
        if metric_def.derived_from:
            data = self._compute_derived_metrics(metric_def, data)

        # Aplicar cálculos post-query si se solicitan
        compute_warnings = []
        if compute:
            data, compute_warnings = self._apply_compute(
                compute, data, dimension_codes, filters or {}
            )

        # Extraer columns del primer row (todos los rows tienen las mismas keys)
        columns = list(data[0].keys()) if data else []

        return {
            "columns": columns,
            "data": data,
            "metadata": {
                "metric": metric_def.code,
                "metric_label": metric_def.label,
                "dimensions": [d.value for d in dimension_codes],
                "total_rows": len(data),
                "source": metric_def.source.value,
                "compute": compute,
                "warnings": compute_warnings if compute_warnings else None,
            },
        }

    def _compute_derived_metrics(
        self,
        metric_def: MetricDefinition,
        data: list[dict],
    ) -> list[dict]:
        """Calcula métricas derivadas post-query."""
        if not metric_def.formula_fn:
            return data

        for row in data:
            derived_value = metric_def.compute_derived(row)
            if derived_value is not None:
                row["valor"] = derived_value

        return data

    def _apply_compute(
        self,
        compute: str,
        data: list[dict],
        dimension_codes: list[DimensionCode],
        filters: dict,
    ) -> tuple[list[dict], list[str]]:
        """
        Aplica cálculos post-query.

        Soporta:
        - "corredor_endemico": Calcula percentiles por semana para múltiples años

        Returns:
            Tuple of (processed_data, warnings)
        """
        if compute == "corredor_endemico":
            return self._compute_corredor_endemico(data, dimension_codes, filters)
        else:
            raise ValueError(
                f"Compute no soportado: {compute}. Opciones: corredor_endemico"
            )

    def _compute_corredor_endemico(
        self,
        data: list[dict],
        dimension_codes: list[DimensionCode],
        filters: dict,
    ) -> tuple[list[dict], list[str]]:
        """
        Calcula corredor endémico a partir de datos multi-año.

        REQUISITOS:
        - Mínimo 2 años históricos (excluyendo 2020-2021)
        """
        import numpy as np  # Disponible via pandas

        MIN_YEARS_VALID = 2
        warnings = []

        if not data:
            return [], ["No hay datos disponibles para calcular el corredor endémico"]

        # 1. Identificar años disponibles
        anios = {
            row.get("anio_epidemiologico")
            for row in data
            if row.get("anio_epidemiologico")
        }
        if not anios:
            return [], ["No se encontraron años en los datos"]

        # Formato unificado de periodo:
        # {"anio_desde": int, "semana_desde": int, "anio_hasta": int, "semana_hasta": int}
        periodo = filters.get("periodo", {})
        anio_actual = periodo.get("anio_hasta") or max(anios)

        # Excluir 2020 y 2021 de los históricos
        anios_historicos = sorted(
            [a for a in anios if a != anio_actual and a not in [2020, 2021]]
        )
        n_anios_hist = len(anios_historicos)

        # 2. Validar suficiencia de datos
        if n_anios_hist < MIN_YEARS_VALID:
            warnings.append(
                f"Datos insuficientes: solo {n_anios_hist} año(s) histórico(s) válido(s) ({', '.join(map(str, anios_historicos))}). "
                f"Se requieren mínimo {MIN_YEARS_VALID} años (excluyendo 2020-2021)."
            )

        # 3. Agrupar por semana separando histórico vs actual
        from collections import defaultdict

        semanas_historicas: dict[int, list[float]] = defaultdict(list)
        semanas_actuales: dict[int, float] = defaultdict(float)

        for row in data:
            semana = row.get("semana_epidemiologica")
            anio = row.get("anio_epidemiologico")
            valor = float(row.get("valor", 0) or 0)

            if semana is None or anio is None:
                continue

            # Skip pandemic years in processing
            if anio in [2020, 2021] and anio != anio_actual:
                continue

            if anio == anio_actual:
                semanas_actuales[semana] += valor
            else:
                semanas_historicas[semana].append(valor)

        # 4. Calcular percentiles y fusionar
        result = []
        todas_semanas = set(semanas_historicas.keys()) | set(semanas_actuales.keys())

        for semana in sorted(todas_semanas):
            valores_hist = semanas_historicas.get(semana, [])
            valor_act = semanas_actuales.get(semana, 0.0)

            # Cálculo de zonas (solo si hay historia suficiente)
            if len(valores_hist) > 0 and n_anios_hist >= MIN_YEARS_VALID:
                p25 = float(np.percentile(valores_hist, 25))
                p50 = float(np.percentile(valores_hist, 50))
                p75 = float(np.percentile(valores_hist, 75))
                p90 = float(np.percentile(valores_hist, 90))

                row_data = {
                    "semana_epidemiologica": semana,
                    "valor_actual": valor_act,
                    "zona_exito": p25,
                    "zona_seguridad": p50,
                    "zona_alerta": p75,
                    "zona_brote": p90,
                    "corredor_valido": True,
                }
            else:
                # Solo datos actuales si no hay suficiente historia
                row_data = {
                    "semana_epidemiologica": semana,
                    "valor_actual": valor_act,
                    "zona_exito": 0,
                    "zona_seguridad": 0,
                    "zona_alerta": 0,
                    "zona_brote": 0,
                    "corredor_valido": False,
                }
            result.append(row_data)

        return result, warnings

"""
BloqueQueryAdapter: Traduce configuración de bloques a queries de MetricService.

Este adapter es el puente entre la configuración declarativa de bloques (DB)
y el sistema de métricas. Resuelve series dinámicamente desde catálogos.
"""

import logging
from dataclasses import dataclass
from typing import Any

from jinja2 import Template
from sqlalchemy.orm import Session, selectinload
from sqlmodel import col, select

from app.domains.boletines.constants import TipoBloque
from app.domains.boletines.models import BoletinBloque
from app.domains.catalogos.agentes.agrupacion import AgrupacionAgentes
from app.domains.metricas.criteria.base import Criterion, EmptyCriterion
from app.domains.metricas.criteria.evento import (
    AgenteCriterion,
    AgrupacionAgentesCriterion,
    TipoEventoCriterion,
)
from app.domains.metricas.criteria.temporal import (
    AniosMultiplesCriterion,
    RangoPeriodoCriterion,
)
from app.domains.metricas.service import MetricService
from app.domains.vigilancia_agregada.models.catalogos import (
    TipoCasoEpidemiologicoPasivo,
)

logger = logging.getLogger(__name__)


@dataclass
class BoletinContexto:
    """Contexto temporal para ejecución de bloques."""

    semana_actual: int
    anio_actual: int
    num_semanas: int = 4  # Ventana de semanas a mostrar
    anios_historicos: list[int] | None = None  # Para corredor endémico

    def __post_init__(self) -> None:
        # anios_historicos se resuelve dinámicamente en el adapter
        # basándose en los años que realmente tienen datos
        pass


@dataclass
class SerieConfig:
    """Configuración de una serie de datos."""

    slug: str
    label: str
    color: str
    criterion: Criterion


@dataclass
class BloqueResultado:
    """Resultado de ejecución de un bloque."""

    bloque_id: int
    slug: str
    titulo: str
    tipo_visualizacion: str
    series: list[dict[str, Any]]
    config_visual: dict[str, Any]
    metadata: dict[str, Any]


class BloqueQueryAdapter:
    """
    Traduce configuración de bloque a queries de MetricService.

    Responsabilidades:
    1. Construir criterios desde criterios_fijos + contexto temporal
    2. Resolver series desde catálogos (AgrupacionAgentes, TipoCasoEpidemiologicoPasivo)
    3. Ejecutar queries via MetricService
    4. Renderizar títulos con Jinja2
    """

    # Cache de años disponibles para evitar queries repetidas
    _anios_disponibles_cache: list[int] | None = None

    def __init__(self, session: Session):
        self.session = session
        self.metric_service = MetricService(session)

    def _get_anios_historicos_disponibles(self, anio_actual: int) -> list[int]:
        """
        Detecta dinámicamente qué años históricos tienen datos disponibles.

        Excluye años de pandemia (2020, 2021) y el año actual.
        Usa cache para evitar queries repetidas.
        """
        if BloqueQueryAdapter._anios_disponibles_cache is not None:
            return [
                a
                for a in BloqueQueryAdapter._anios_disponibles_cache
                if a != anio_actual and a not in (2020, 2021)
            ]

        from sqlalchemy import distinct

        from app.domains.vigilancia_agregada.models.cargas import NotificacionSemanal

        # Query para obtener años únicos con datos
        stmt = select(distinct(col(NotificacionSemanal.anio))).order_by(
            col(NotificacionSemanal.anio)
        )
        result = self.session.execute(stmt)
        todos_anios = [row[0] for row in result.fetchall()]

        # Guardar en cache
        BloqueQueryAdapter._anios_disponibles_cache = todos_anios

        # Filtrar: excluir pandemia y año actual
        anios_historicos = [
            a for a in todos_anios if a != anio_actual and a not in (2020, 2021)
        ]

        logger.info(f"     Años disponibles en DB: {todos_anios}")
        logger.info(
            f"     Años históricos para corredor (excl. {anio_actual}, 2020-2021): {anios_historicos}"
        )

        return anios_historicos

    def ejecutar_bloque(
        self,
        bloque: BoletinBloque,
        contexto: BoletinContexto,
    ) -> BloqueResultado:
        """
        Ejecuta un bloque y retorna sus datos.

        Args:
            bloque: Configuración del bloque desde BD
            contexto: Contexto temporal (semana, año, etc.)

        Returns:
            BloqueResultado con series de datos
        """
        # 1. Construir criterio base
        criterio_base = self._construir_criterio_base(bloque, contexto)
        logger.info(f"     Bloque: {bloque.slug}, criterio_base: {criterio_base}")

        # 2. Resolver series
        series = self._resolver_series(bloque)
        logger.info(
            f"     Series resueltas: {len(series)} ({[s.slug for s in series]})"
        )

        # 3. Determinar compute (corredor_endemico si aplica)
        compute = self._determinar_compute(bloque)
        logger.info(
            f"     Compute: {compute}, métrica: {bloque.metrica_codigo}, dims: {bloque.dimensiones}"
        )

        # 4. Ejecutar query por cada serie
        resultados_series = []
        for serie in series:
            criterio_final = (
                criterio_base & serie.criterion if serie.criterion else criterio_base
            )
            logger.info(f"       Serie '{serie.slug}': ejecutando query...")

            try:
                result = self.metric_service.query(
                    metric=bloque.metrica_codigo,
                    dimensions=bloque.dimensiones,
                    criteria=criterio_final,
                    compute=compute,
                    filters={
                        "periodo": {
                            "anio_desde": contexto.anio_actual,
                            "semana_desde": max(
                                1, contexto.semana_actual - contexto.num_semanas + 1
                            ),
                            "anio_hasta": contexto.anio_actual,
                            "semana_hasta": contexto.semana_actual,
                        }
                    },
                )
                data_count = len(result.get("data", []))
                logger.info(f"       Serie '{serie.slug}': {data_count} filas de datos")
                if data_count > 0:
                    logger.info(f"       Muestra de datos: {result['data'][:2]}")
                resultados_series.append(
                    {
                        "serie": serie.label,
                        "slug": serie.slug,
                        "color": serie.color,
                        "data": result["data"],
                        "metadata": result["metadata"],
                    }
                )
            except Exception as e:
                # Log error pero continuar con otras series
                logger.error(f"       Serie '{serie.slug}': ERROR - {e}")
                resultados_series.append(
                    {
                        "serie": serie.label,
                        "slug": serie.slug,
                        "color": serie.color,
                        "data": [],
                        "error": str(e),
                    }
                )

        # 5. Renderizar título
        titulo = self._render_titulo(bloque, contexto, len(resultados_series))

        return BloqueResultado(
            bloque_id=bloque.id,  # type: ignore[arg-type]
            slug=bloque.slug,
            titulo=titulo,
            tipo_visualizacion=bloque.tipo_visualizacion.value,
            series=resultados_series,
            config_visual=bloque.config_visual,
            metadata={
                "tipo_bloque": bloque.tipo_bloque.value,
                "metrica": bloque.metrica_codigo,
                "dimensiones": bloque.dimensiones,
                "compute": compute,
            },
        )

    def _construir_criterio_base(
        self,
        bloque: BoletinBloque,
        contexto: BoletinContexto,
    ) -> Criterion:
        """
        Construye criterio base desde criterios_fijos + contexto.

        El rango temporal se determina por (en orden de prioridad):
        1. config_visual.rango_temporal del bloque (si existe)
        2. Tipo de bloque (corredor_endemico usa años históricos)
        3. Default: últimas num_semanas semanas

        Opciones de rango_temporal en config_visual:
        - "anio_completo": SE 1 hasta SE actual del año actual
        - "ultimas_N_semanas": N semanas hacia atrás (ej: "ultimas_6_semanas")
        - "historico_desde_YYYY": Desde año YYYY hasta actual (ej: "historico_desde_2014")
        - "anios_multiples": Lista de años específicos
        """
        criterios: list[Criterion] = []
        config = bloque.config_visual or {}
        rango_temporal = config.get("rango_temporal")

        # Determinar criterio temporal
        if rango_temporal:
            criterios.append(self._parse_rango_temporal(rango_temporal, contexto))
        elif bloque.tipo_bloque == TipoBloque.CORREDOR_ENDEMICO:
            # Corredor necesita múltiples años históricos + actual
            # Si no se especifican años históricos, detectar dinámicamente
            if contexto.anios_historicos:
                anios_hist = list(contexto.anios_historicos)
            else:
                anios_hist = self._get_anios_historicos_disponibles(
                    contexto.anio_actual
                )
            anios = anios_hist + [contexto.anio_actual]
            criterios.append(AniosMultiplesCriterion(anios=anios))
        else:
            # Default: últimas num_semanas semanas
            semana_desde = max(1, contexto.semana_actual - contexto.num_semanas + 1)
            criterios.append(
                RangoPeriodoCriterion(
                    anio_desde=contexto.anio_actual,
                    semana_desde=semana_desde,
                    anio_hasta=contexto.anio_actual,
                    semana_hasta=contexto.semana_actual,
                )
            )

        # Criterios fijos del bloque
        criterios_fijos = bloque.criterios_fijos or {}

        if "tipo_evento_slug" in criterios_fijos:
            criterios.append(
                TipoEventoCriterion(slug=criterios_fijos["tipo_evento_slug"])
            )

        if "tipo_evento_id" in criterios_fijos:
            criterios.append(
                TipoEventoCriterion(ids=[criterios_fijos["tipo_evento_id"]])
            )

        if "tipo_evento_nombre" in criterios_fijos:
            # Búsqueda por nombre parcial (ilike)
            criterios.append(
                TipoEventoCriterion(nombre=criterios_fijos["tipo_evento_nombre"])
            )

        if "agrupacion_slug" in criterios_fijos:
            criterios.append(
                AgrupacionAgentesCriterion(slug=criterios_fijos["agrupacion_slug"])
            )

        # Combinar todos con AND
        if not criterios:
            return EmptyCriterion()

        resultado = criterios[0]
        for c in criterios[1:]:
            resultado = resultado & c
        return resultado

    def _resolver_series(self, bloque: BoletinBloque) -> list[SerieConfig]:
        """
        Resuelve series desde catálogos de BD o config manual.

        Formatos de series_source:
        - "agrupacion:<categoria>": Series desde AgrupacionAgentes (ej: "agrupacion:respiratorio")
        - "eventos:<categoria>": Series desde TipoCasoEpidemiologicoPasivo
        - None o "manual": Usar series_config del bloque
        """
        if not bloque.series_source or bloque.series_source == "manual":
            return self._series_from_config(bloque.series_config or [])

        parts = bloque.series_source.split(":", 1)
        if len(parts) != 2:
            return self._series_from_config(bloque.series_config or [])

        source_type, source_value = parts

        if source_type == "agrupacion":
            return self._series_from_agrupaciones(source_value)
        elif source_type == "eventos":
            return self._series_from_eventos(source_value)
        else:
            return self._series_from_config(bloque.series_config or [])

    def _series_from_config(self, config: list[dict[str, Any]]) -> list[SerieConfig]:
        """Series desde configuración manual."""
        series = []
        for item in config:
            criterion: Criterion = EmptyCriterion()

            # Construir criterio según tipo
            if "tipo_evento_slug" in item:
                criterion = TipoEventoCriterion(slug=item["tipo_evento_slug"])
            elif "agrupacion_slug" in item:
                criterion = AgrupacionAgentesCriterion(slug=item["agrupacion_slug"])
            elif "agente_ids" in item:
                criterion = AgenteCriterion(ids=item["agente_ids"])

            series.append(
                SerieConfig(
                    slug=item.get("slug", item.get("label", "unknown")),
                    label=item.get("label", "Sin nombre"),
                    color=item.get("color", "#6B7280"),
                    criterion=criterion,
                )
            )
        return series

    def _series_from_agrupaciones(self, categoria: str) -> list[SerieConfig]:
        """Series desde AgrupacionAgentes por categoría."""
        stmt = (
            select(AgrupacionAgentes)
            .options(selectinload(AgrupacionAgentes.agentes))  # type: ignore[arg-type]
            .where(col(AgrupacionAgentes.categoria) == categoria)
            .where(col(AgrupacionAgentes.activo).is_(True))
            .order_by(col(AgrupacionAgentes.orden))
        )
        agrupaciones = self.session.execute(stmt).scalars().all()

        series = []
        for agrup in agrupaciones:
            # Obtener IDs de agentes de esta agrupación
            agente_ids = [a.id for a in agrup.agentes]

            series.append(
                SerieConfig(
                    slug=agrup.slug,
                    label=agrup.nombre_corto,
                    color=agrup.color,
                    criterion=AgenteCriterion(ids=agente_ids)  # type: ignore[arg-type]
                    if agente_ids
                    else EmptyCriterion(),
                )
            )
        return series

    def _series_from_eventos(self, categoria: str) -> list[SerieConfig]:
        """
        Series desde TipoCasoEpidemiologicoPasivo.

        La categoría se interpreta como grupo_nombre o como lista de slugs
        separados por coma.
        """
        # Si contiene comas, es una lista de slugs
        if "," in categoria:
            slugs = [s.strip() for s in categoria.split(",")]
            stmt = select(TipoCasoEpidemiologicoPasivo).where(
                col(TipoCasoEpidemiologicoPasivo.slug).in_(slugs)
            )
        else:
            # Buscar por grupo_nombre
            stmt = select(TipoCasoEpidemiologicoPasivo).where(
                col(TipoCasoEpidemiologicoPasivo.grupo_nombre).ilike(f"%{categoria}%")
            )

        eventos = self.session.execute(stmt).scalars().all()

        # Colores predeterminados para eventos
        colores_default = [
            "#2196F3",
            "#F44336",
            "#4CAF50",
            "#FF9800",
            "#9C27B0",
            "#00BCD4",
            "#795548",
            "#E91E63",
            "#3F51B5",
            "#009688",
        ]

        series = []
        for i, evento in enumerate(eventos):
            series.append(
                SerieConfig(
                    slug=evento.slug,
                    label=evento.nombre,
                    color=colores_default[i % len(colores_default)],
                    criterion=TipoEventoCriterion(slug=evento.slug),
                )
            )
        return series

    def _parse_rango_temporal(
        self,
        rango_temporal: str,
        contexto: BoletinContexto,
    ) -> Criterion:
        """
        Parsea configuración de rango temporal a criterio.

        Formatos soportados:
        - "anio_completo": SE 1 hasta SE actual
        - "ultimas_6_semanas": últimas 6 semanas
        - "historico_desde_2014": desde 2014 hasta año actual
        - "anios:2018,2019,2022,2023,2024": años específicos
        """
        import re

        # Año completo (SE 1 hasta SE actual)
        if rango_temporal == "anio_completo":
            return RangoPeriodoCriterion(
                anio_desde=contexto.anio_actual,
                semana_desde=1,
                anio_hasta=contexto.anio_actual,
                semana_hasta=contexto.semana_actual,
            )

        # Últimas N semanas
        match = re.match(r"ultimas_(\d+)_semanas", rango_temporal)
        if match:
            n_semanas = int(match.group(1))
            semana_desde = max(1, contexto.semana_actual - n_semanas + 1)
            return RangoPeriodoCriterion(
                anio_desde=contexto.anio_actual,
                semana_desde=semana_desde,
                anio_hasta=contexto.anio_actual,
                semana_hasta=contexto.semana_actual,
            )

        # Histórico desde año YYYY
        match = re.match(r"historico_desde_(\d{4})", rango_temporal)
        if match:
            anio_desde = int(match.group(1))
            anios = list(range(anio_desde, contexto.anio_actual + 1))
            return AniosMultiplesCriterion(anios=anios)

        # Años específicos
        match = re.match(r"anios:(.+)", rango_temporal)
        if match:
            anios_str = match.group(1)
            anios = [int(a.strip()) for a in anios_str.split(",")]
            return AniosMultiplesCriterion(anios=anios)

        # Default: año completo
        return RangoPeriodoCriterion(
            anio_desde=contexto.anio_actual,
            semana_desde=1,
            anio_hasta=contexto.anio_actual,
            semana_hasta=contexto.semana_actual,
        )

    def _determinar_compute(self, bloque: BoletinBloque) -> str | None:
        """Determina qué compute aplicar según tipo de bloque."""
        if bloque.compute:
            return bloque.compute

        # Inferir de tipo_bloque
        if bloque.tipo_bloque == TipoBloque.CORREDOR_ENDEMICO:
            return "corredor_endemico"

        return None

    def _render_titulo(
        self,
        bloque: BoletinBloque,
        contexto: BoletinContexto,
        num_series: int,
    ) -> str:
        """Renderiza título con Jinja2."""
        try:
            template = Template(bloque.titulo_template)
            return template.render(
                semana=contexto.semana_actual,
                anio=contexto.anio_actual,
                num_semanas=contexto.num_semanas,
                num_series=num_series,
            )
        except Exception:
            return bloque.titulo_template

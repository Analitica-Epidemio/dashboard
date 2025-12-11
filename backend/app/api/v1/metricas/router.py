"""
Endpoints de la API de métricas.

Provee acceso unificado al Metric Service para dashboards,
boletines y BI explorer.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User
from app.domains.metricas.criteria.base import Criterion
from app.domains.metricas.criteria.evento import (
    AgenteCriterion,
    TipoEventoCriterion,
)
from app.domains.metricas.criteria.temporal import (
    RangoPeriodoCriterion,
)
from app.domains.metricas.schema import (  # Generado dinámicamente
    get_cube_schema,
    list_cubes,
)
from app.domains.metricas.service import MetricService

router = APIRouter(prefix="/metricas", tags=["metricas"])


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════


class PeriodoFilter(BaseModel):
    """Filtro de período temporal unificado. Soporta rangos que cruzan años."""

    anio_desde: int = Field(..., description="Año de inicio", ge=2000, le=2100)
    semana_desde: int = Field(..., description="Semana de inicio (1-53)", ge=1, le=53)
    anio_hasta: int = Field(..., description="Año de fin", ge=2000, le=2100)
    semana_hasta: int = Field(..., description="Semana de fin (1-53)", ge=1, le=53)

    @model_validator(mode="after")
    def validar_rango(self):
        """Valida que el rango sea coherente (inicio <= fin)."""
        if self.anio_desde > self.anio_hasta:
            raise ValueError("anio_desde debe ser menor o igual a anio_hasta")
        if self.anio_desde == self.anio_hasta and self.semana_desde > self.semana_hasta:
            raise ValueError(
                "semana_desde debe ser menor o igual a semana_hasta en el mismo año"
            )
        return self

    def calcular_semanas(self) -> int:
        """Calcula el número total de semanas en el rango."""
        if self.anio_desde == self.anio_hasta:
            return self.semana_hasta - self.semana_desde + 1

        # Cruzando años
        semanas_anio_inicio = 52 - self.semana_desde + 1
        semanas_anio_fin = self.semana_hasta
        anios_intermedios = self.anio_hasta - self.anio_desde - 1
        return semanas_anio_inicio + (anios_intermedios * 52) + semanas_anio_fin


class ComparacionTipo(str):
    """Tipos de comparación disponibles."""

    YOY = "yoy"  # Mismo período, año anterior
    PERIODO_ANTERIOR = "periodo_anterior"  # Período inmediatamente anterior


class MetricFilters(BaseModel):
    """Filtros unificados para queries de métricas."""

    # Temporal - REQUERIDO
    periodo: PeriodoFilter = Field(..., description="Período a consultar")

    # Filtros de evento - single o multiple
    evento_id: int | None = Field(None, description="ID de tipo de evento (single)")
    evento_ids: list[int] | None = Field(
        None, description="IDs de tipos de evento (multi-select)"
    )
    evento_nombre: str | None = Field(None, description="Nombre parcial de evento")

    # Filtros de grupo ENO
    grupo_id: int | None = Field(None, description="ID de grupo ENO (single)")
    grupo_ids: list[int] | None = Field(
        None, description="IDs de grupos ENO (multi-select)"
    )

    # Filtros de agente - individual o agrupación
    agente_id: int | None = Field(None, description="ID de agente etiológico (single)")
    agente_ids: list[int] | None = Field(
        None, description="IDs de agentes etiológicos (multi-select)"
    )
    agente_nombre: str | None = Field(None, description="Nombre parcial de agente")
    agrupacion_slug: str | None = Field(
        None,
        description="Slug de agrupación de agentes (ej: 'influenza-a'). Resuelve a múltiples agente_ids.",
    )

    # Filtros geográficos
    provincia_id: int | None = Field(None, description="ID INDEC de provincia")
    provincia_nombre: str | None = Field(None, description="Nombre de provincia")
    departamento_id: int | None = Field(None, description="ID INDEC de departamento")
    establecimiento_id: int | None = Field(None, description="ID de establecimiento")


class MetricQueryRequest(BaseModel):
    """Request para query de métricas."""

    metric: str = Field(..., description="Código de la métrica (ej: casos_clinicos)")
    dimensions: list[str] = Field(
        default=[],
        description="Dimensiones para agrupar (ej: [SEMANA_EPIDEMIOLOGICA, TIPO_EVENTO])",
    )
    filters: MetricFilters = Field(..., description="Filtros a aplicar")
    compute: str | None = Field(
        default=None,
        description="Cálculo post-query: 'corredor_endemico'",
    )


class MetricQueryMetadata(BaseModel):
    """Metadata de respuesta de query."""

    metric: str
    metric_label: str | None = None
    dimensions: list[str]
    total_rows: int
    source: str | None = None
    compute: str | None = None
    warnings: list[str] | None = None


class MetricDataRow(BaseModel):
    """
    Fila de datos de métrica con todas las dimensiones posibles.

    Los campos que vienen en cada response dependen de las dimensiones
    solicitadas. El campo 'columns' en MetricQueryResponse indica
    qué campos están presentes.
    """

    # === Valor principal ===
    valor: int | float | None = None
    valor_actual: int | float | None = None
    valor_anterior: int | float | None = None

    # === Dimensiones temporales ===
    semana_epidemiologica: int | None = None
    anio_epidemiologico: int | None = None

    # === Dimensiones geográficas ===
    provincia: str | None = None
    departamento: str | None = None
    establecimiento: str | None = None

    # === Dimensiones demográficas ===
    grupo_etario: str | None = None
    sexo: str | None = None

    # === Dimensiones de clasificación ===
    tipo_evento: str | None = None
    agente_etiologico: str | None = None
    agrupacion: str | None = None
    tecnica: str | None = None

    # === Corredor endémico ===
    zona_exito: float | None = None
    zona_seguridad: float | None = None
    zona_alerta: float | None = None
    zona_brote: float | None = None
    corredor_valido: bool | None = None

    # === Comparación ===
    delta_porcentaje: float | None = None
    tendencia: str | None = None

    model_config = {"extra": "allow"}  # Permite campos adicionales por si acaso


class MetricQueryResponse(BaseModel):
    """Response de query de métricas."""

    columns: list[str] = Field(
        ..., description="Lista de campos presentes en cada fila de data"
    )
    data: list[MetricDataRow]
    metadata: MetricQueryMetadata


# Tipos para corredor endémico
class CorredorEndemicoRow(BaseModel):
    """Fila de datos de corredor endémico."""

    semana_epidemiologica: int
    valor_actual: float
    zona_exito: float
    zona_seguridad: float
    zona_alerta: float
    zona_brote: float
    corredor_valido: bool


# Tipos para distribución de agentes
class AgenteSemanaRow(BaseModel):
    """Distribución de agentes por semana."""

    semana: int
    agentes: dict[str, int]
    total: int


class AgenteEdadRow(BaseModel):
    """Distribución de agentes por grupo etario."""

    grupo_etario: str
    agentes: dict[str, int]
    total: int


# Tipos para ocupación hospitalaria
class OcupacionCamasRow(BaseModel):
    """Datos de ocupación de camas."""

    establecimiento: str
    camas_totales: int
    camas_ocupadas: int
    porcentaje_ocupacion: float
    tipo_cama: str


class MetricInfoResponse(BaseModel):
    """Información de métricas disponibles."""

    metrics: list[dict]
    dimensions: list[dict]


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/schema")
def get_schema(
    current_user: User = Depends(RequireAnyRole()),
) -> dict[str, Any]:
    """
    Lista todos los cubes disponibles para el BI Engine.

    Retorna información sobre cada tipo de vigilancia incluyendo:
    - Métricas disponibles
    - Dimensiones para agrupar
    - Filtros aplicables
    - Visualizaciones permitidas
    - KPIs predefinidos
    """
    return {"cubes": list_cubes()}


@router.get("/schema/{cube_id}")
def get_cube_detail(
    cube_id: str,
    current_user: User = Depends(RequireAnyRole()),
) -> dict[str, Any]:
    """
    Obtiene el schema completo de un cube específico.

    Útil para construir dinámicamente la UI de una página de vigilancia.
    """
    schema = get_cube_schema(cube_id)
    if not schema:
        raise HTTPException(status_code=404, detail=f"Cube '{cube_id}' no encontrado")
    return schema


@router.get("/disponibles", response_model=MetricInfoResponse)
def get_available_metrics(
    session: Session = Depends(get_session),
    current_user: User = Depends(RequireAnyRole()),
) -> MetricInfoResponse:
    """
    Lista métricas y dimensiones disponibles.

    Útil para construir UI de query builder dinámicamente.
    """
    service = MetricService(session)
    return MetricInfoResponse(
        metrics=service.list_available_metrics(),
        dimensions=service.list_available_dimensions(),
    )


@router.post("/query", response_model=MetricQueryResponse)
def query_metric(
    request: MetricQueryRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(RequireAnyRole()),
) -> MetricQueryResponse:
    """
    Query unificado para cualquier métrica.

    Ejemplos de uso:

    1. Casos de ETI por semana en 2025:
    ```json
    {
        "metric": "casos_clinicos",
        "dimensions": ["SEMANA_EPIDEMIOLOGICA"],
        "filters": {"anio": 2025, "evento_nombre": "ETI"}
    }
    ```

    2. Muestras de laboratorio por agente:
    ```json
    {
        "metric": "muestras_estudiadas",
        "dimensions": ["AGENTE_ETIOLOGICO"],
        "filters": {"anio": 2025}
    }
    ```

    3. Distribución por grupo etario:
    ```json
    {
        "metric": "casos_clinicos",
        "dimensions": ["GRUPO_ETARIO"],
        "filters": {"anio": 2025, "semana": 48}
    }
    ```
    """
    import logging

    logger = logging.getLogger(__name__)

    logger.info(
        f"📊 Métrica query: metric={request.metric}, dims={request.dimensions}, filters={request.filters}"
    )

    service = MetricService(session)

    # Parsear filtros a Criteria
    try:
        criteria = _parse_filters_to_criteria(request.filters)
    except Exception as e:
        logger.error(f"❌ Error parseando filtros: {e}")
        raise HTTPException(status_code=400, detail=f"Error en filtros: {str(e)}")

    # Convertir a dict para compute functions
    filters_dict = _filters_to_dict(request.filters)

    try:
        result = service.query(
            metric=request.metric,
            dimensions=request.dimensions,
            criteria=criteria,
            compute=request.compute,
            filters=filters_dict,  # Dict para compute functions
        )
    except ValueError as e:
        logger.error(f"❌ ValueError en query: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except NotImplementedError as e:
        logger.error(f"❌ NotImplementedError: {e}")
        raise HTTPException(status_code=501, detail=str(e))

    return MetricQueryResponse(**result)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════


def _parse_filters_to_criteria(filters: MetricFilters) -> Criterion | None:
    """
    Convierte MetricFilters tipado a Criteria type-safe.

    Usa el nuevo modelo unificado con periodo obligatorio.
    """
    from app.domains.metricas.criteria.geografico import (
        DepartamentoCriterion,
        EstablecimientoCriterion,
        ProvinciaCriterion,
    )

    criteria = None
    periodo = filters.periodo

    # Filtro temporal - siempre usamos RangoPeriodoCriterion (soporta multi-año)
    criteria = RangoPeriodoCriterion(
        anio_desde=periodo.anio_desde,
        semana_desde=periodo.semana_desde,
        anio_hasta=periodo.anio_hasta,
        semana_hasta=periodo.semana_hasta,
    )

    # Filtros de evento - prioridad: evento_ids > evento_id > evento_nombre
    if filters.evento_ids:
        c = TipoEventoCriterion(ids=filters.evento_ids)
        criteria = criteria & c
    elif filters.evento_id:
        c = TipoEventoCriterion(ids=[filters.evento_id])
        criteria = criteria & c
    elif filters.evento_nombre:
        c = TipoEventoCriterion(nombre=filters.evento_nombre)
        criteria = criteria & c

    # Filtros de agente - prioridad: agrupacion_slug > agente_ids > agente_id > agente_nombre
    # Si hay agrupacion_slug, se resuelve a lista de agente_ids
    if filters.agrupacion_slug:
        # Importación lazy para evitar circular
        from app.domains.catalogos.agentes.seed_agrupaciones import (
            get_agente_ids_for_agrupacion,
        )

        # Obtener session actual via contexto o crear nueva
        # Nota: esto requiere que se pase session desde el router
        # Por ahora, resolvemos via import directo
        try:
            from sqlmodel import Session

            from app.core.database import engine

            with Session(engine) as temp_session:
                agente_ids = get_agente_ids_for_agrupacion(
                    temp_session, filters.agrupacion_slug
                )
            if agente_ids:
                c = AgenteCriterion(ids=agente_ids)
                criteria = criteria & c
        except Exception as e:
            import logging

            logging.getLogger(__name__).warning(
                f"Error resolviendo agrupacion {filters.agrupacion_slug}: {e}"
            )
    elif filters.agente_ids:
        c = AgenteCriterion(ids=filters.agente_ids)
        criteria = criteria & c
    elif filters.agente_id:
        c = AgenteCriterion(ids=[filters.agente_id])
        criteria = criteria & c
    elif filters.agente_nombre:
        c = AgenteCriterion(nombre=filters.agente_nombre)
        criteria = criteria & c

    # Filtros geográficos - prioridad: provincia_id > provincia_nombre
    if filters.provincia_id:
        c = ProvinciaCriterion(ids=[filters.provincia_id])
        criteria = criteria & c
    elif filters.provincia_nombre:
        c = ProvinciaCriterion(nombre=filters.provincia_nombre)
        criteria = criteria & c

    if filters.departamento_id:
        c = DepartamentoCriterion(ids=[filters.departamento_id])
        criteria = criteria & c

    if filters.establecimiento_id:
        c = EstablecimientoCriterion(ids=[filters.establecimiento_id])
        criteria = criteria & c

    return criteria


def _filters_to_dict(filters: MetricFilters) -> dict:
    """
    Convierte MetricFilters a dict para pasar a compute functions.
    """
    return {
        "periodo": {
            "anio_desde": filters.periodo.anio_desde,
            "semana_desde": filters.periodo.semana_desde,
            "anio_hasta": filters.periodo.anio_hasta,
            "semana_hasta": filters.periodo.semana_hasta,
        },
    }

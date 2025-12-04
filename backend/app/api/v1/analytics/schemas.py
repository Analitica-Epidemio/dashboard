"""
Analytics schemas
"""

from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PeriodType(str, Enum):
    """Tipos de períodos predefinidos"""
    ULTIMA_SEMANA_EPI = "ULTIMA_SEMANA_EPI"
    ULTIMAS_4_SEMANAS_EPI = "ULTIMAS_4_SEMANAS_EPI"
    ULTIMAS_12_SEMANAS_EPI = "ULTIMAS_12_SEMANAS_EPI"
    MES_HASTA_FECHA = "MES_HASTA_FECHA"
    MES_PASADO = "MES_PASADO"
    ULTIMOS_3_MESES = "ULTIMOS_3_MESES"
    TRIMESTRE_ACTUAL = "TRIMESTRE_ACTUAL"
    TRIMESTRE_PASADO = "TRIMESTRE_PASADO"
    ULTIMOS_6_MESES = "ULTIMOS_6_MESES"
    ANIO_HASTA_FECHA = "ANIO_HASTA_FECHA"
    ANIO_PASADO = "ANIO_PASADO"
    PERSONALIZADO = "PERSONALIZADO"


class ComparisonType(str, Enum):
    """Tipo de comparación a realizar"""
    ROLLING = "ROLLING"  # Comparar vs período anterior del mismo tamaño
    YEAR_OVER_YEAR = "YEAR_OVER_YEAR"  # Comparar vs mismo período año anterior
    BOTH = "BOTH"  # Mostrar ambas comparaciones


class PeriodInfo(BaseModel):
    """Información de un período de tiempo"""
    fecha_desde: date = Field(..., description="Fecha de inicio del período")
    fecha_hasta: date = Field(..., description="Fecha de fin del período")
    semana_epi_desde: Optional[int] = Field(None, description="Semana epidemiológica de inicio")
    semana_epi_hasta: Optional[int] = Field(None, description="Semana epidemiológica de fin")
    anio_epi: Optional[int] = Field(None, description="Año epidemiológico")
    descripcion: str = Field(..., description="Descripción legible del período")


class MetricValue(BaseModel):
    """Valor de una métrica con su comparación"""
    valor_actual: float = Field(..., description="Valor en el período actual")
    valor_anterior: Optional[float] = Field(None, description="Valor en el período de comparación")
    diferencia_absoluta: Optional[float] = Field(None, description="Diferencia absoluta (actual - anterior)")
    diferencia_porcentual: Optional[float] = Field(None, description="Diferencia porcentual ((actual - anterior) / anterior * 100)")
    tendencia: Optional[str] = Field(None, description="up, down o stable")


class CasosMetrics(BaseModel):
    """Métricas de casos confirmados"""
    total_casos: MetricValue = Field(..., description="Total de casos confirmados")
    incidencia_100k: MetricValue = Field(..., description="Tasa de incidencia por 100k habitantes")
    promedio_semanal: MetricValue = Field(..., description="Promedio de casos por semana")
    casos_por_semana: List[Dict[str, Any]] = Field(..., description="Serie temporal de casos por semana")


class CoberturaMetrics(BaseModel):
    """Métricas de cobertura geográfica"""
    areas_afectadas: MetricValue = Field(..., description="Número de departamentos con casos")
    nuevas_areas: int = Field(..., description="Departamentos que reportaron casos por primera vez")
    areas_sin_casos: int = Field(..., description="Departamentos que dejaron de reportar casos")
    top_departamentos: List[Dict[str, Any]] = Field(..., description="Top departamentos por casos")


class PerformanceMetrics(BaseModel):
    """Métricas de performance de clasificación"""
    tasa_confirmacion: MetricValue = Field(..., description="% de casos confirmados vs total")
    tiempo_promedio_clasificacion: Optional[MetricValue] = Field(None, description="Días promedio entre consulta y clasificación")
    casos_en_estudio: MetricValue = Field(..., description="Casos aún en proceso de clasificación")
    confianza_promedio: MetricValue = Field(..., description="Score de confianza promedio de clasificación")


class AnalyticsResponse(BaseModel):
    """Response completo del endpoint de analytics"""
    periodo_actual: PeriodInfo = Field(..., description="Información del período actual")
    periodo_comparacion: Optional[PeriodInfo] = Field(None, description="Información del período de comparación")
    tipo_comparacion: ComparisonType = Field(..., description="Tipo de comparación realizada")

    # Métricas principales
    casos: CasosMetrics = Field(..., description="Métricas de casos confirmados")
    cobertura: CoberturaMetrics = Field(..., description="Métricas de cobertura geográfica")
    performance: PerformanceMetrics = Field(..., description="Métricas de performance")

    # Filtros aplicados
    filtros_aplicados: Dict[str, Any] = Field(..., description="Filtros aplicados a la consulta")


class TopWinnerLoser(BaseModel):
    """Item en lista de top winners/losers"""
    entidad_id: int = Field(..., description="ID de la entidad (departamento, tipo_eno, etc)")
    entidad_nombre: str = Field(..., description="Nombre de la entidad")
    valor_actual: float = Field(..., description="Valor en período actual")
    valor_anterior: float = Field(..., description="Valor en período anterior")
    diferencia_porcentual: float = Field(..., description="% de cambio")
    diferencia_absoluta: float = Field(..., description="Cambio absoluto")


class TopWinnersLosersResponse(BaseModel):
    """Response de top winners y losers"""
    top_winners: List[TopWinnerLoser] = Field(..., description="Entidades con mayor mejora")
    top_losers: List[TopWinnerLoser] = Field(..., description="Entidades con mayor deterioro")
    metric_type: str = Field(..., description="Tipo de métrica analizada")
    periodo_actual: PeriodInfo
    periodo_comparacion: PeriodInfo


# ============================================================================
# Schemas para el nuevo sistema de Analytics con Boletines
# ============================================================================

class EventoCambio(BaseModel):
    """Evento con su cambio entre dos períodos"""
    tipo_eno_id: int = Field(..., description="ID del tipo de evento")
    tipo_eno_nombre: str = Field(..., description="Nombre del evento")
    grupo_eno_id: int = Field(..., description="ID del grupo epidemiológico")
    grupo_eno_nombre: str = Field(..., description="Nombre del grupo")
    casos_actuales: int = Field(..., description="Casos en período actual")
    casos_anteriores: int = Field(..., description="Casos en período anterior")
    diferencia_absoluta: int = Field(..., description="Diferencia absoluta de casos")
    diferencia_porcentual: float = Field(..., description="% de cambio")
    tasa_incidencia_actual: Optional[float] = Field(None, description="Tasa por 100k habitantes en período actual")
    tasa_incidencia_anterior: Optional[float] = Field(None, description="Tasa por 100k habitantes en período anterior")


class GrupoConCambios(BaseModel):
    """Grupo epidemiológico con sus eventos de mayor crecimiento/decrecimiento"""
    grupo_id: int = Field(..., description="ID del grupo")
    grupo_nombre: str = Field(..., description="Nombre del grupo")
    top_crecimiento: List[EventoCambio] = Field(..., description="Top eventos con mayor crecimiento")
    top_decrecimiento: List[EventoCambio] = Field(..., description="Top eventos con mayor decrecimiento")


class PeriodoAnalisis(BaseModel):
    """Información de un período de análisis epidemiológico"""
    semana_inicio: int = Field(..., description="Semana epidemiológica de inicio")
    semana_fin: int = Field(..., description="Semana epidemiológica de fin")
    anio: int = Field(..., description="Año epidemiológico")
    fecha_inicio: date = Field(..., description="Fecha de inicio del período")
    fecha_fin: date = Field(..., description="Fecha de fin del período")


class TopChangesByGroupResponse(BaseModel):
    """Response de top cambios GLOBALES (sin agrupar por grupo)"""
    periodo_actual: PeriodoAnalisis = Field(..., description="Período actual analizado")
    periodo_anterior: PeriodoAnalisis = Field(..., description="Período de comparación")
    top_crecimiento: List[EventoCambio] = Field(..., description="Top 10 eventos con mayor crecimiento")
    top_decrecimiento: List[EventoCambio] = Field(..., description="Top 10 eventos con mayor decrecimiento")


class CalculateChangesRequest(BaseModel):
    """Request para calcular cambios de eventos custom"""
    tipo_eno_ids: List[int] = Field(..., description="IDs de eventos a calcular")
    semana_actual: int = Field(..., description="Semana epidemiológica actual", ge=1, le=53)
    anio_actual: int = Field(..., description="Año epidemiológico actual")
    num_semanas: int = Field(default=4, description="Número de semanas hacia atrás", ge=1, le=52)


class EventoCambioConCategoria(EventoCambio):
    """Evento con cambio y su categoría automática"""
    categoria: str = Field(..., description="Categoría: 'crecimiento' o 'decrecimiento'")


class CalculateChangesResponse(BaseModel):
    """Response de cambios calculados para eventos custom"""
    eventos: List[EventoCambioConCategoria] = Field(..., description="Eventos con sus cambios calculados")


class TrendSemanal(BaseModel):
    """Punto en la serie temporal semanal"""
    semana: int = Field(..., description="Semana epidemiológica")
    anio: int = Field(..., description="Año epidemiológico")
    casos: int = Field(..., description="Número de casos")
    periodo: str = Field(..., description="'actual' o 'anterior'")


class ResumenEvento(BaseModel):
    """Resumen del evento para el dialog de detalles"""
    casos_actuales: int = Field(..., description="Casos en período actual")
    casos_anteriores: int = Field(..., description="Casos en período anterior")
    diferencia_porcentual: float = Field(..., description="% de cambio")
    diferencia_absoluta: int = Field(..., description="Cambio absoluto")


class TipoEnoBasic(BaseModel):
    """Información básica de un tipo de evento"""
    id: int
    nombre: str
    codigo: Optional[str] = None


class GrupoEnoBasic(BaseModel):
    """Información básica de un grupo epidemiológico"""
    id: int
    nombre: str
    descripcion: Optional[str] = None


class EventoDetailsResponse(BaseModel):
    """Response con detalles completos de un evento para el dialog"""
    tipo_eno: TipoEnoBasic = Field(..., description="Información del tipo de evento")
    grupo_eno: GrupoEnoBasic = Field(..., description="Información del grupo epidemiológico")
    resumen: ResumenEvento = Field(..., description="Resumen del cambio")
    trend_semanal: List[TrendSemanal] = Field(..., description="Serie temporal por semana")

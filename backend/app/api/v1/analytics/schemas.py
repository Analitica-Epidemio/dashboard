"""
Analytics schemas
"""

from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PeriodType(str, Enum):
    """Tipos de períodos predefinidos"""
    ULTIMA_SEMANA_EPI = "ultima_semana_epi"
    ULTIMAS_4_SEMANAS_EPI = "ultimas_4_semanas_epi"
    ULTIMAS_12_SEMANAS_EPI = "ultimas_12_semanas_epi"
    MES_HASTA_FECHA = "mes_hasta_fecha"
    MES_PASADO = "mes_pasado"
    ULTIMOS_3_MESES = "ultimos_3_meses"
    TRIMESTRE_ACTUAL = "trimestre_actual"
    TRIMESTRE_PASADO = "trimestre_pasado"
    ULTIMOS_6_MESES = "ultimos_6_meses"
    ANIO_HASTA_FECHA = "anio_hasta_fecha"
    ANIO_PASADO = "anio_pasado"
    PERSONALIZADO = "personalizado"


class ComparisonType(str, Enum):
    """Tipo de comparación a realizar"""
    ROLLING = "rolling"  # Comparar vs período anterior del mismo tamaño
    YEAR_OVER_YEAR = "year_over_year"  # Comparar vs mismo período año anterior
    BOTH = "both"  # Mostrar ambas comparaciones


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

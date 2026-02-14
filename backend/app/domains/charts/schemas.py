"""
Universal Chart Specification
Schemas Pydantic para la especificación universal de charts
Compatibles con los tipos TypeScript del frontend
"""

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any, ClassVar, Literal

from pydantic import BaseModel, Field

# ============================================================================
# Tipos Base
# ============================================================================


class CodigoGrafico(StrEnum):
    """Códigos canónicos de gráficos soportados por el ChartSpecGenerator."""

    CURVA_EPIDEMIOLOGICA = "curva_epidemiologica"
    CORREDOR_ENDEMICO = "corredor_endemico"
    PIRAMIDE_EDAD = "piramide_edad"
    MAPA_CHUBUT = "mapa_chubut"
    ESTACIONALIDAD = "estacionalidad"
    CASOS_EDAD = "casos_edad"
    DISTRIBUCION_CLASIFICACION = "distribucion_clasificacion"
    CASOS_POR_SEMANA = "casos_por_semana"  # Alias de CURVA_EPIDEMIOLOGICA


TipoGrafico = Literal["line", "bar", "area", "pie", "d3_pyramid", "mapa"]


class MetadataSemana(BaseModel):
    """Metadata de semana epidemiológica"""

    anio: int = Field(..., serialization_alias="year")
    semana: int = Field(..., serialization_alias="week")
    fecha_inicio: str = Field(..., serialization_alias="start_date")
    fecha_fin: str = Field(..., serialization_alias="end_date")


class ConjuntoDatos(BaseModel):
    """Dataset para charts line/bar/area/pie"""

    etiqueta: str | None = Field(None, serialization_alias="label")
    datos: list[float] = Field(..., serialization_alias="data")
    color: str | None = None
    tipo: Literal["area", "line"] | None = Field(
        None, serialization_alias="type"
    )  # Para area charts con líneas


# ============================================================================
# Datos por Tipo de Chart
# ============================================================================


class DatosGraficoBase(BaseModel):
    """Datos para line, bar, area, pie charts"""

    etiquetas: list[str] = Field(..., serialization_alias="labels")
    conjuntos_datos: list[ConjuntoDatos] = Field(..., serialization_alias="datasets")
    metadata: list[MetadataSemana] | None = None


class PuntoDatosPiramide(BaseModel):
    """Punto de datos para pirámide poblacional"""

    grupo_edad: str = Field(..., serialization_alias="age_group")
    masculino: float = Field(..., serialization_alias="male")
    femenino: float = Field(..., serialization_alias="female")


class DatosDepartamentoMapa(BaseModel):
    """Datos de departamento para mapa"""

    codigo_indec: int
    nombre: str
    zona_ugd: str
    poblacion: int
    casos: int
    tasa_incidencia: float


class DatosGraficoMapa(BaseModel):
    """Datos para mapa de Chubut"""

    departamentos: list[DatosDepartamentoMapa]
    total_casos: int


# ============================================================================
# Discriminated Union Wrappers para Data
# ============================================================================


class DatosGraficoLinea(BaseModel):
    """Wrapper con discriminador para line chart data"""

    tipo: Literal["line"] = Field("line", serialization_alias="type")
    datos: DatosGraficoBase = Field(..., serialization_alias="data")


class DatosGraficoBarra(BaseModel):
    """Wrapper con discriminador para bar chart data"""

    tipo: Literal["bar"] = Field("bar", serialization_alias="type")
    datos: DatosGraficoBase = Field(..., serialization_alias="data")


class DatosGraficoArea(BaseModel):
    """Wrapper con discriminador para area chart data"""

    tipo: Literal["area"] = Field("area", serialization_alias="type")
    datos: DatosGraficoBase = Field(..., serialization_alias="data")


class DatosGraficoTorta(BaseModel):
    """Wrapper con discriminador para pie chart data"""

    tipo: Literal["pie"] = Field("pie", serialization_alias="type")
    datos: DatosGraficoBase = Field(..., serialization_alias="data")


class DatosGraficoPiramide(BaseModel):
    """Wrapper con discriminador para pyramid chart data"""

    tipo: Literal["d3_pyramid"] = Field("d3_pyramid", serialization_alias="type")
    datos: list[PuntoDatosPiramide] = Field(..., serialization_alias="data")


class WrapperDatosGraficoMapa(BaseModel):
    """Wrapper con discriminador para map chart data"""

    tipo: Literal["mapa"] = Field("mapa", serialization_alias="type")
    datos: DatosGraficoMapa = Field(..., serialization_alias="data")


# Union discriminada para todos los tipos de datos
UnionDatosGrafico = Annotated[
    DatosGraficoLinea | DatosGraficoBarra | DatosGraficoArea | DatosGraficoTorta | DatosGraficoPiramide | WrapperDatosGraficoMapa,
    Field(discriminator="tipo"),
]


# ============================================================================
# Configuración de Charts
# ============================================================================


class ConfiguracionGraficoBase(BaseModel):
    """Configuración base para todos los charts"""

    alto: int | None = Field(None, serialization_alias="height")
    ancho: int | None = Field(None, serialization_alias="width")
    mostrar_leyenda: bool | None = Field(True, serialization_alias="showLegend")
    mostrar_grilla: bool | None = Field(True, serialization_alias="showGrid")
    colores: list[str] | None = Field(None, serialization_alias="colors")


class ConfiguracionGraficoLinea(ConfiguracionGraficoBase):
    """Configuración específica para line charts"""

    mostrar_puntos: bool | None = Field(True, serialization_alias="showPoints")
    curvado: bool | None = Field(False, serialization_alias="curved")


class ConfiguracionGraficoBarra(ConfiguracionGraficoBase):
    """Configuración específica para bar charts"""

    apilado: bool | None = Field(False, serialization_alias="stacked")
    horizontal: bool | None = False


class ConfiguracionGraficoArea(ConfiguracionGraficoBase):
    """Configuración específica para area charts"""

    apilado: bool | None = Field(False, serialization_alias="stacked")
    opacidad_relleno: float | None = Field(0.6, serialization_alias="fillOpacity")


class ConfiguracionGraficoTorta(ConfiguracionGraficoBase):
    """Configuración específica para pie charts"""

    mostrar_porcentajes: bool | None = Field(
        True, serialization_alias="showPercentages"
    )
    radio_interno: int | None = Field(
        0, serialization_alias="innerRadius"
    )  # For donut charts


class ConfiguracionGraficoPiramide(ConfiguracionGraficoBase):
    """Configuración específica para pyramid charts"""

    mostrar_etiquetas_ejes: bool | None = True


class ConfiguracionGraficoMapa(ConfiguracionGraficoBase):
    """Configuración específica para map charts"""

    escala_color: Literal["sequential", "diverging"] | None = "sequential"
    provincia: Literal["chubut"] | None = "chubut"


# ============================================================================
# Discriminated Union Wrappers para Config
# ============================================================================


class WrapperConfiguracionGraficoLinea(BaseModel):
    """Wrapper con discriminador para line chart config"""

    tipo: Literal["line"] = Field("line", serialization_alias="type")
    configuracion: ConfiguracionGraficoLinea = Field(..., serialization_alias="config")


class WrapperConfiguracionGraficoBarra(BaseModel):
    """Wrapper con discriminador para bar chart config"""

    tipo: Literal["bar"] = Field("bar", serialization_alias="type")
    configuracion: ConfiguracionGraficoBarra = Field(..., serialization_alias="config")


class WrapperConfiguracionGraficoArea(BaseModel):
    """Wrapper con discriminador para area chart config"""

    tipo: Literal["area"] = Field("area", serialization_alias="type")
    configuracion: ConfiguracionGraficoArea = Field(..., serialization_alias="config")


class WrapperConfiguracionGraficoTorta(BaseModel):
    """Wrapper con discriminador para pie chart config"""

    tipo: Literal["pie"] = Field("pie", serialization_alias="type")
    configuracion: ConfiguracionGraficoTorta = Field(..., serialization_alias="config")


class WrapperConfiguracionGraficoPiramide(BaseModel):
    """Wrapper con discriminador para pyramid chart config"""

    tipo: Literal["d3_pyramid"] = Field("d3_pyramid", serialization_alias="type")
    configuracion: ConfiguracionGraficoPiramide = Field(
        ..., serialization_alias="config"
    )


class WrapperConfiguracionGraficoMapa(BaseModel):
    """Wrapper con discriminador para map chart config"""

    tipo: Literal["mapa"] = Field("mapa", serialization_alias="type")
    configuracion: ConfiguracionGraficoMapa = Field(..., serialization_alias="config")


# Union discriminada para todos los tipos de config
UnionConfiguracionGrafico = Annotated[
    WrapperConfiguracionGraficoLinea | WrapperConfiguracionGraficoBarra | WrapperConfiguracionGraficoArea | WrapperConfiguracionGraficoTorta | WrapperConfiguracionGraficoPiramide | WrapperConfiguracionGraficoMapa,
    Field(discriminator="tipo"),
]


# ============================================================================
# Filtros (para reproducibilidad)
# ============================================================================

AgrupacionTemporal = Literal["semana", "mes", "anio"]


class FiltrosGrafico(BaseModel):
    """Filtros aplicados al chart (para reproducibilidad)"""

    ids_grupo_eno: list[int] | None = None
    ids_tipo_eno: list[int] | None = None
    clasificacion: list[str] | None = None
    id_provincia: list[int] | None = None
    fecha_desde: str | None = None
    fecha_hasta: str | None = None
    edad_min: int | None = None
    edad_max: int | None = None
    tipo_sujeto: Literal["humano", "animal"] | None = None
    # Filtros de período epidemiológico
    anio: int | None = None  # Año epidemiológico
    semana_desde: int | None = None  # Semana epidemiológica inicio
    semana_hasta: int | None = None  # Semana epidemiológica fin
    # Agrupación temporal
    agrupacion_temporal: AgrupacionTemporal | None = (
        "semana"  # Agrupar por semana, mes o año
    )
    # Comparaciones
    comparar_anio_anterior: bool | None = False  # Incluir línea de año anterior
    comparar_periodo_anterior: bool | None = False  # Incluir período anterior
    extra: dict[str, Any] | None = Field(default_factory=dict)


# ============================================================================
# Especificación Universal
# ============================================================================


class ErrorGrafico(BaseModel):
    """Error estructurado para charts que no pueden generarse"""

    codigo: str = Field(
        ..., serialization_alias="code"
    )  # Código de error (ej: "INSUFFICIENT_HISTORICAL_DATA")
    titulo: str = Field(..., serialization_alias="title")  # Título corto para mostrar
    mensaje: str = Field(
        ..., serialization_alias="message"
    )  # Mensaje descriptivo para el usuario
    detalles: dict[str, Any] | None = Field(
        None, serialization_alias="details"
    )  # Detalles técnicos opcionales
    sugerencia: str | None = Field(
        None, serialization_alias="suggestion"
    )  # Sugerencia de cómo resolver


class EspecificacionGraficoUniversal(BaseModel):
    """
    Especificación universal de chart
    Puede ser usada tanto por frontend como backend
    """

    # Metadata
    id: str
    titulo: str = Field(..., serialization_alias="title")
    descripcion: str | None = Field(None, serialization_alias="description")
    codigo: str | None = None

    # Tipo de chart
    tipo: TipoGrafico = Field(..., serialization_alias="type")

    # Datos (con discriminador type para TypeScript)
    datos: UnionDatosGrafico = Field(..., serialization_alias="data")

    # Config (con discriminador type para TypeScript)
    configuracion: UnionConfiguracionGrafico = Field(..., serialization_alias="config")

    # Filtros aplicados (para reproducibilidad)
    filtros: FiltrosGrafico | None = None

    # Error (si el chart no pudo generarse correctamente)
    error: ErrorGrafico | None = None

    # Timestamp
    generado_en: str | None = Field(
        default_factory=lambda: datetime.now().isoformat(),
        serialization_alias="generated_at",
    )

    class Config:
        json_schema_extra: ClassVar[dict[str, Any]] = {
            "example": {
                "id": "chart_001",
                "titulo": "Casos por Semana Epidemiológica",
                "tipo": "line",
                "datos": {
                    "etiquetas": ["SE 1", "SE 2", "SE 3"],
                    "conjuntos_datos": [
                        {"etiqueta": "Confirmados", "datos": [10, 15, 12]},
                    ],
                },
                "configuracion": {"alto": 400, "mostrar_leyenda": True},
            }
        }


# ============================================================================
# Request/Response para API
# ============================================================================


class SolicitudSpecGrafico(BaseModel):
    """Request para obtener spec de un chart"""

    codigo_grafico: CodigoGrafico
    filtros: FiltrosGrafico
    configuracion: dict[str, Any] | None = None


class RespuestaSpecGrafico(BaseModel):
    """Response con el spec generado"""

    spec: EspecificacionGraficoUniversal
    generado_en: str

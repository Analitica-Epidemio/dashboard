"""Schemas para endpoints de mapeo de establecimientos."""


from pydantic import BaseModel, Field


class SugerenciaMapeo(BaseModel):
    """Sugerencia de mapeo SNVS → IGN."""

    id_establecimiento_ign: int
    nombre_ign: str
    codigo_refes: str | None
    localidad_nombre: str | None
    departamento_nombre: str | None
    provincia_nombre: str | None
    similitud_nombre: float
    score: float
    confianza: str  # HIGH, MEDIUM, LOW
    razon: str
    provincia_match: bool
    departamento_match: bool
    localidad_match: bool


class EstablecimientoSinMapear(BaseModel):
    """Establecimiento SNVS sin mapear a IGN."""

    id: int
    nombre: str
    codigo_snvs: str | None
    localidad_nombre: str | None
    departamento_nombre: str | None
    provincia_nombre: str | None
    total_eventos: int  # Número de eventos asociados
    sugerencias: list[SugerenciaMapeo] = []


class EstablecimientosSinMapearResponse(BaseModel):
    """Respuesta de establecimientos sin mapear."""

    items: list[EstablecimientoSinMapear]
    total: int
    sin_mapear_count: int  # Total de establecimientos sin código REFES
    eventos_sin_mapear_count: int  # Total de eventos sin geolocalizar


class EstablecimientoIGNResult(BaseModel):
    """Resultado de búsqueda de establecimientos IGN."""

    id: int
    nombre: str
    codigo_refes: str | None
    localidad_nombre: str | None
    departamento_nombre: str | None
    provincia_nombre: str | None
    latitud: float | None
    longitud: float | None


class BuscarIGNResponse(BaseModel):
    """Respuesta de búsqueda de establecimientos IGN."""

    items: list[EstablecimientoIGNResult]
    total: int
    page: int
    page_size: int


class CrearMapeoRequest(BaseModel):
    """Request para crear un mapeo SNVS → IGN."""

    id_establecimiento_snvs: int = Field(
        ..., description="ID del establecimiento SNVS (source='SNVS')"
    )
    id_establecimiento_ign: int = Field(
        ..., description="ID del establecimiento IGN (source='IGN')"
    )
    razon: str | None = Field(None, description="Razón del mapeo")


class ActualizarMapeoRequest(BaseModel):
    """Request para actualizar un mapeo existente."""

    id_establecimiento_ign_nuevo: int = Field(
        ..., description="Nuevo ID del establecimiento IGN"
    )
    razon: str | None = Field(None, description="Nueva razón del mapeo")


class MapeoInfo(BaseModel):
    """Información de un mapeo existente."""

    id_establecimiento_snvs: int
    nombre_snvs: str
    codigo_snvs: str | None
    id_establecimiento_ign: int | None
    nombre_ign: str
    codigo_refes: str | None
    mapeo_score: float | None
    mapeo_similitud_nombre: float | None
    mapeo_confianza: str | None
    mapeo_razon: str | None
    mapeo_es_manual: bool | None
    mapeo_validado: bool | None
    total_eventos: int
    localidad_nombre_snvs: str | None
    localidad_nombre_ign: str | None
    provincia_nombre_snvs: str | None
    provincia_nombre_ign: str | None


class MapeosListResponse(BaseModel):
    """Respuesta de lista de mapeos."""

    items: list[MapeoInfo]
    total: int
    page: int
    page_size: int


class AceptarSugerenciasBulkRequest(BaseModel):
    """Request para aceptar múltiples sugerencias."""

    mapeos: list[CrearMapeoRequest] = Field(..., description="Lista de mapeos a crear")


class EstadisticasMapeosResponse(BaseModel):
    """Estadísticas generales de mapeos."""

    total_establecimientos_snvs: int
    establecimientos_sin_mapear: int
    establecimientos_mapeados: int
    eventos_totales: int
    eventos_sin_geolocalizar: int
    cobertura_eventos_porcentaje: float  # % de eventos con geolocalización

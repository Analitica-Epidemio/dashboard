"""Schemas para endpoints de mapeo de establecimientos."""

from typing import List, Optional

from pydantic import BaseModel, Field


class SugerenciaMapeo(BaseModel):
    """Sugerencia de mapeo SNVS → IGN."""

    id_establecimiento_ign: int
    nombre_ign: str
    codigo_refes: Optional[str]
    localidad_nombre: Optional[str]
    departamento_nombre: Optional[str]
    provincia_nombre: Optional[str]
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
    codigo_snvs: Optional[str]
    localidad_nombre: Optional[str]
    departamento_nombre: Optional[str]
    provincia_nombre: Optional[str]
    total_eventos: int  # Número de eventos asociados
    sugerencias: List[SugerenciaMapeo] = []


class EstablecimientosSinMapearResponse(BaseModel):
    """Respuesta de establecimientos sin mapear."""

    items: List[EstablecimientoSinMapear]
    total: int
    sin_mapear_count: int  # Total de establecimientos sin código REFES
    eventos_sin_mapear_count: int  # Total de eventos sin geolocalizar


class EstablecimientoIGNResult(BaseModel):
    """Resultado de búsqueda de establecimientos IGN."""

    id: int
    nombre: str
    codigo_refes: Optional[str]
    localidad_nombre: Optional[str]
    departamento_nombre: Optional[str]
    provincia_nombre: Optional[str]
    latitud: Optional[float]
    longitud: Optional[float]


class BuscarIGNResponse(BaseModel):
    """Respuesta de búsqueda de establecimientos IGN."""

    items: List[EstablecimientoIGNResult]
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
    razon: Optional[str] = Field(None, description="Razón del mapeo")


class ActualizarMapeoRequest(BaseModel):
    """Request para actualizar un mapeo existente."""

    id_establecimiento_ign_nuevo: int = Field(
        ..., description="Nuevo ID del establecimiento IGN"
    )
    razon: Optional[str] = Field(None, description="Nueva razón del mapeo")


class MapeoInfo(BaseModel):
    """Información de un mapeo existente."""

    id_establecimiento_snvs: int
    nombre_snvs: str
    codigo_snvs: Optional[str]
    id_establecimiento_ign: Optional[int]
    nombre_ign: str
    codigo_refes: Optional[str]
    mapeo_score: Optional[float]
    mapeo_similitud_nombre: Optional[float]
    mapeo_confianza: Optional[str]
    mapeo_razon: Optional[str]
    mapeo_es_manual: Optional[bool]
    mapeo_validado: Optional[bool]
    total_eventos: int
    localidad_nombre_snvs: Optional[str]
    localidad_nombre_ign: Optional[str]
    provincia_nombre_snvs: Optional[str]
    provincia_nombre_ign: Optional[str]


class MapeosListResponse(BaseModel):
    """Respuesta de lista de mapeos."""

    items: List[MapeoInfo]
    total: int
    page: int
    page_size: int


class AceptarSugerenciasBulkRequest(BaseModel):
    """Request para aceptar múltiples sugerencias."""

    mapeos: List[CrearMapeoRequest] = Field(..., description="Lista de mapeos a crear")


class EstadisticasMapeosResponse(BaseModel):
    """Estadísticas generales de mapeos."""

    total_establecimientos_snvs: int
    establecimientos_sin_mapear: int
    establecimientos_mapeados: int
    eventos_totales: int
    eventos_sin_geolocalizar: int
    cobertura_eventos_porcentaje: float  # % de eventos con geolocalización

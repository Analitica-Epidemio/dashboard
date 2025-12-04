"""Router para endpoints de establecimientos."""

from fastapi import APIRouter

from app.core.schemas.response import ErrorResponse, SuccessResponse

from .aceptar_bulk import aceptar_sugerencias_bulk
from .actualizar_mapeo import actualizar_mapeo_snvs_ign
from .buscar_ign import buscar_establecimientos_ign_endpoint
from .crear_mapeo import crear_mapeo_snvs_ign
from .eliminar_mapeo import eliminar_mapeo_snvs_ign
from .get_detalle import EstablecimientoDetalleResponse, get_establecimiento_detalle
from .get_sin_mapear import get_establecimientos_sin_mapear
from .list import EstablecimientosMapaResponse, get_establecimientos_mapa
from .list_con_eventos import (
    EstablecimientosListResponse,
    list_establecimientos_con_eventos,
)
from .list_mapeos import listar_mapeos_existentes

# Endpoints de mapeo SNVS → IGN
from .mapeo_schemas import (
    BuscarIGNResponse,
    EstablecimientosSinMapearResponse,
    MapeosListResponse,
)

router = APIRouter(prefix="/establecimientos", tags=["Establecimientos"])

# ============================================================================
# ENDPOINTS EXISTENTES
# ============================================================================

router.add_api_route(
    "/mapa",
    get_establecimientos_mapa,
    methods=["GET"],
    response_model=SuccessResponse[EstablecimientosMapaResponse],
    summary="Obtener establecimientos para mapa",
    description="Obtiene establecimientos de salud geocodificados para visualización en mapa",
)

# Endpoint de listado de establecimientos con conteo de eventos
router.add_api_route(
    "",
    list_establecimientos_con_eventos,
    methods=["GET"],
    response_model=SuccessResponse[EstablecimientosListResponse],
    summary="Listar establecimientos con eventos",
    description="Lista establecimientos con conteo de eventos relacionados",
)

# Endpoint de detalle de establecimiento con sus personas/eventos relacionados
router.add_api_route(
    "/{id_establecimiento}",
    get_establecimiento_detalle,
    methods=["GET"],
    response_model=SuccessResponse[EstablecimientoDetalleResponse],
    summary="Obtener detalle de establecimiento",
    description="Obtiene detalle completo de un establecimiento con todas las personas/eventos relacionados",
    responses={
        404: {"model": ErrorResponse, "description": "Establecimiento no encontrado"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    },
)

# ============================================================================
# ENDPOINTS DE MAPEO SNVS → IGN
# ============================================================================

# Obtener establecimientos sin mapear con sugerencias
router.add_api_route(
    "/sin-mapear",
    get_establecimientos_sin_mapear,
    methods=["GET"],
    response_model=SuccessResponse[EstablecimientosSinMapearResponse],
    summary="Obtener establecimientos sin mapear",
    description="Lista establecimientos SNVS sin mapear a IGN, con sugerencias automáticas priorizadas por impacto (eventos)",
)

# Buscar establecimientos IGN
router.add_api_route(
    "/ign/buscar",
    buscar_establecimientos_ign_endpoint,
    methods=["GET"],
    response_model=SuccessResponse[BuscarIGNResponse],
    summary="Buscar establecimientos IGN",
    description="Busca establecimientos IGN por nombre o código REFES con filtros geográficos",
)

# Listar mapeos existentes
router.add_api_route(
    "/mapeos",
    listar_mapeos_existentes,
    methods=["GET"],
    response_model=SuccessResponse[MapeosListResponse],
    summary="Listar mapeos existentes",
    description="Lista mapeos SNVS → IGN existentes con metadata y opciones de filtrado",
)

# Crear mapeo
router.add_api_route(
    "/mapeos",
    crear_mapeo_snvs_ign,
    methods=["POST"],
    response_model=SuccessResponse[dict],
    summary="Crear mapeo SNVS → IGN",
    description="Crea un mapeo manual entre un establecimiento SNVS y uno IGN",
    responses={
        404: {"model": ErrorResponse, "description": "Establecimiento no encontrado"},
        400: {"model": ErrorResponse, "description": "Establecimiento ya tiene mapeo"},
    },
)

# Actualizar mapeo
router.add_api_route(
    "/mapeos/{id_establecimiento_snvs}",
    actualizar_mapeo_snvs_ign,
    methods=["PUT"],
    response_model=SuccessResponse[dict],
    summary="Actualizar mapeo existente",
    description="Actualiza un mapeo existente apuntando a un nuevo establecimiento IGN",
    responses={
        404: {"model": ErrorResponse, "description": "Establecimiento no encontrado"},
        400: {"model": ErrorResponse, "description": "Establecimiento no tiene mapeo"},
    },
)

# Eliminar mapeo
router.add_api_route(
    "/mapeos/{id_establecimiento_snvs}",
    eliminar_mapeo_snvs_ign,
    methods=["DELETE"],
    response_model=SuccessResponse[dict],
    summary="Eliminar mapeo (desvincular)",
    description="Elimina un mapeo existente, removiendo el código REFES y metadata",
    responses={
        404: {"model": ErrorResponse, "description": "Establecimiento no encontrado"},
        400: {"model": ErrorResponse, "description": "Establecimiento no tiene mapeo"},
    },
)

# Aceptar múltiples sugerencias en bulk
router.add_api_route(
    "/mapeos/bulk",
    aceptar_sugerencias_bulk,
    methods=["POST"],
    response_model=SuccessResponse[dict],
    summary="Aceptar múltiples sugerencias en bulk",
    description="Crea múltiples mapeos en una sola operación (útil para aceptar sugerencias de alta confianza)",
)

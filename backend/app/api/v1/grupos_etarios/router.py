from fastapi import APIRouter, HTTPException
from app.core.schemas.response import SuccessResponse, ErrorResponse
from .schemas import (
    ConfiguracionRangosCreate,
    ConfiguracionRangosOut,
)
from .service import list_configs, create_config, delete_config

router = APIRouter(prefix="/grupos_etarios")

# GET
router.add_api_route(
    "/",
    lambda: SuccessResponse(data=list_configs()),
    methods=["GET"],
    response_model=SuccessResponse[list[ConfiguracionRangosOut]],
)

# POST
def _crear(payload: ConfiguracionRangosCreate):
    obj = create_config(payload)
    return SuccessResponse(data=obj)

router.add_api_route(
    "/",
    _crear,
    methods=["POST"],
    response_model=SuccessResponse[ConfiguracionRangosOut],
)

# DELETE
def _delete(config_id: int):
    ok = delete_config(config_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    return SuccessResponse(data=True)

router.add_api_route(
    "/{config_id}",
    _delete,
    methods=["DELETE"],
    response_model=SuccessResponse[bool],
)


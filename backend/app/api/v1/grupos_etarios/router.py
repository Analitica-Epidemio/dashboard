from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse

from .schemas import (
    ConfiguracionRangosCreate,
    ConfiguracionRangosOut,
)
from .service import create_config, delete_config, list_configs

router = APIRouter(prefix="/grupos_etarios")


# GET
async def _listar(
    session: AsyncSession = Depends(get_async_session),
) -> SuccessResponse[list[ConfiguracionRangosOut]]:
    data = await list_configs(session)
    return SuccessResponse(data=data)


router.add_api_route(
    "/",
    _listar,
    methods=["GET"],
    response_model=SuccessResponse[list[ConfiguracionRangosOut]],
)


# POST
async def _crear(
    payload: ConfiguracionRangosCreate,
    session: AsyncSession = Depends(get_async_session),
) -> SuccessResponse[ConfiguracionRangosOut]:
    obj = await create_config(payload, session)
    return SuccessResponse(data=obj)


router.add_api_route(
    "/",
    _crear,
    methods=["POST"],
    response_model=SuccessResponse[ConfiguracionRangosOut],
)


# DELETE
async def _delete(
    config_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> SuccessResponse[bool]:
    ok = await delete_config(config_id, session)
    if not ok:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    return SuccessResponse(data=True)


router.add_api_route(
    "/{config_id}",
    _delete,
    methods=["DELETE"],
    response_model=SuccessResponse[bool],
)

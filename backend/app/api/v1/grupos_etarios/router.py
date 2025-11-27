from fastapi import APIRouter

from app.core.schemas.response import ErrorResponse, SuccessResponse
from app.domains.grupos_etarios.gruposetarios_models import ConfiguracionRangos
from app.core.database import get_async_session
from app.core.query_builders import EventoQueryBuilder
from .schemas import RangoEdadSchema, ConfiguracionRangosCreate, ConfiguracionRangosOut
from .service import list_configuracion_rangos, create_configuracion_rangos, delete_configuracion_rangos

router = APIRouter(prefix="/grupos_etarios")

# GET
router.add_api_route(
    "/",
    lambda: SuccessResponse(data=list_configuracion_rangos()),
    methods=["GET"],
    response_model=SuccessResponse[list[ConfiguracionRangosOut]],
)

# POST
# router.py
@router.post("/")
async def _crear(
    payload: ConfiguracionRangosCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole())
):
    return await create_configuracion_rangos(payload, db, current_user)


# DELETE
async def _delete(config_id: int):
    ok = await delete_configuracion_rangos(config_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    return SuccessResponse(data=True)

router.add_api_route(
    "/{config_id}",
    _delete,
    methods=["DELETE"],
    response_model=SuccessResponse[bool],
)

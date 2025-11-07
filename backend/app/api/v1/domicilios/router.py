"""Router para endpoints de domicilios"""

from fastapi import APIRouter

from app.core.schemas.response import SuccessResponse

from .list import DomiciliosListResponse, list_domicilios

router = APIRouter(prefix="/domicilios", tags=["Domicilios"])

# Listar domicilios
router.add_api_route(
    "",
    list_domicilios,
    methods=["GET"],
    response_model=SuccessResponse[DomiciliosListResponse],
    summary="Listar domicilios con eventos",
)

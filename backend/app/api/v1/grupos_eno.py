from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.core.database import get_async_session
from app.core.schemas.response import ErrorResponse, SuccessResponse
from app.domains.eventos.models import GrupoEno
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/gruposEno", tags=["GruposENO"])


class GrupoEnoInfo(BaseModel):
    nombre: str = Field(..., max_length=150, description="Nombre del grupo ENO")
    descripcion: Optional[str] = Field(
        None, max_length=500, description="Descripción del grupo"
    )
    codigo: Optional[str] = Field(
        None, max_length=200, unique=True, index=True, description="Código del grupo"
    )

class GrupoEnoResponse(BaseModel):
    items: List[GrupoEnoInfo] = Field(..., description="Grupos ENO")

@router.get(
        "/",
        response_model=GrupoEnoResponse,
        responses={
        500: {"model": ErrorResponse, "description": "Error interno del servidor"}
    },
)
async def list_gruposEno(
    db: AsyncSession = Depends(get_async_session),
) -> GrupoEnoResponse:
    try:
        query = (
            select(GrupoEno)
        )
        result = await db.execute(query)
        gruposEno = result.scalars().all()
        return gruposEno
    except Exception as e:
        logger.error(f"💥 Error listando eventos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo grupos de eventos: {str(e)}",
        )
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.core.database import get_async_session
from app.core.schemas.response import ErrorResponse, SuccessResponse
from app.domains.eventos.models import TipoEno
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tiposEno", tags=["TiposENO"])

class TipoEnoInfo(BaseModel):
    nombre: str = Field(..., max_length=200, description="Nombre del tipo ENO")
    descripcion: Optional[str] = Field(
        None, max_length=500, description="Descripción del tipo"
    )
    codigo: Optional[str] = Field(
        None, max_length=200, unique=True, index=True, description="Código del tipo"
    )

    # Foreign Keys
    id_grupo_eno: int = Field(
        foreign_key="grupo_eno.id", description="ID del grupo ENO"
    )

class TipoEnoResponse(BaseModel):
    items: List[TipoEnoInfo] = Field(..., description="Tipos ENO")

@router.get(
        "/",
        response_model=TipoEnoResponse,
        responses={
        500: {"model": ErrorResponse, "description": "Error interno del servidor"}
    },
)
async def list_tiposEno(
    db: AsyncSession = Depends(get_async_session),
) -> TipoEnoResponse:
    try:
        query = (
            select(TipoEno)
        )
        result = await db.execute(query)
        tiposEno = result.scalars().all()
        return tiposEno
    except Exception as e:
        logger.error(f"💥 Error listando eventos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo eventos: {str(e)}",
        )
"""
API endpoints para analytics y visualizaciones epidemiológicas.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.schemas.response import SuccessResponse
from app.domains.analytics.schemas import (
    DatosVisualizacionRequest,
    DatosVisualizacionResponse,
    GrupoEventoResponse,
    ListaGruposResponse,
)
from app.domains.analytics.services import get_analytics_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/grupos",
    response_model=SuccessResponse[ListaGruposResponse],
    summary="Obtener grupos de eventos disponibles",
)
async def get_grupos(session: Session = Depends(get_session)):
    """
    Obtiene la lista de grupos de eventos disponibles para analytics.

    Incluye tanto eventos simples como grupos de eventos epidemiológicos
    con sus configuraciones de clasificaciones y gráficos especiales.
    """
    try:
        service = get_analytics_service(session)
        grupos = await service.get_grupos()

        logger.info(f"Grupos obtenidos: {grupos.total}")
        return SuccessResponse(data=grupos)

    except Exception as e:
        logger.error(f"Error obteniendo grupos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo grupos: {str(e)}",
        )


@router.get(
    "/grupos/{grupo_id}",
    response_model=SuccessResponse[GrupoEventoResponse],
    summary="Obtener detalle de un grupo específico",
)
async def get_grupo_detalle(grupo_id: int, session: Session = Depends(get_session)):
    """
    Obtiene el detalle de un grupo específico incluyendo:
    - Información del grupo
    - Lista de eventos dentro del grupo
    - Gráficos disponibles para este grupo
    - Estadísticas básicas de cada evento
    """
    try:
        service = get_analytics_service(session)
        grupo = await service.get_grupo_detalle(grupo_id)

        if not grupo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Grupo {grupo_id} no encontrado",
            )

        logger.info(f"Grupo {grupo_id} obtenido: {grupo.grupo.nombre}")
        return SuccessResponse(data=grupo)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo grupo {grupo_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo grupo: {str(e)}",
        )


@router.post(
    "/datos",
    response_model=SuccessResponse[DatosVisualizacionResponse],
    summary="Obtener datos para visualización",
)
async def get_datos_visualizacion(
    request: DatosVisualizacionRequest, session: Session = Depends(get_session)
):
    """
    Obtiene datos procesados para una visualización específica.

    Parámetros:
    - grupo_id: ID del grupo de eventos
    - evento_ids: Lista de eventos específicos (opcional, por defecto todos del grupo)
    - clasificacion: Filtro de clasificación (confirmados, sospechosos, todos)
    - fecha_desde/fecha_hasta: Rango de fechas (opcional)
    - tipo_grafico: Tipo de gráfico solicitado
    - parametros_extra: Parámetros adicionales específicos del gráfico

    Respuesta incluye:
    - Datos formateados según el tipo de gráfico
    - Metadatos del query y filtros aplicados
    - Información contextual (total casos, fecha generación, etc.)
    """
    try:
        service = get_analytics_service(session)
        datos = await service.get_datos_visualizacion(request)

        logger.info(
            f"Datos generados para grupo {request.grupo_id}, gráfico {request.tipo_grafico}: {datos.total_casos} casos"
        )
        return SuccessResponse(data=datos)

    except ValueError as e:
        logger.warning(f"Request inválido: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error generando datos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando datos: {str(e)}",
        )


@router.get(
    "/grupos/{grupo_id}/preview",
    response_model=SuccessResponse[dict],
    summary="Vista previa rápida de un grupo",
)
async def get_preview_grupo(
    grupo_id: int, clasificacion: str = "todos", session: Session = Depends(get_session)
):
    """
    Obtiene una vista previa rápida de un grupo con estadísticas básicas.
    Útil para mostrar información sin cargar datos completos de visualización.
    """
    try:
        service = get_analytics_service(session)

        # Generar un request básico para obtener totales
        request = DatosVisualizacionRequest(
            grupo_id=grupo_id, clasificacion=clasificacion, tipo_grafico="totales"
        )

        datos = await service.get_datos_visualizacion(request)

        preview = {
            "grupo": datos.grupo,
            "eventos": datos.eventos,
            "total_casos": datos.total_casos,
            "clasificacion": datos.clasificacion,
            "filtros_activos": len(datos.filtros_aplicados),
            "ultima_actualizacion": datos.fecha_generacion,
        }

        return SuccessResponse(data=preview)

    except Exception as e:
        logger.error(f"Error generando preview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando preview: {str(e)}",
        )

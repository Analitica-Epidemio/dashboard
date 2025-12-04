"""
List agentes etiológicos endpoint con estadísticas
"""

import logging
from typing import List, Optional

from fastapi import Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import asc, case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.schemas.response import PaginatedResponse, PaginationMeta
from app.core.security import RequireAnyRole
from app.domains.autenticacion.models import User
from app.domains.eventos_epidemiologicos.agentes.models import (
    AgenteEtiologico,
    EventoAgente,
    ResultadoDeteccion,
)

logger = logging.getLogger(__name__)


class AgenteEtiologicoInfo(BaseModel):
    """Información de un agente etiológico con estadísticas"""
    id: int = Field(..., description="ID del agente")
    codigo: str = Field(..., description="Código único del agente")
    nombre: str = Field(..., description="Nombre completo")
    nombre_corto: str = Field(..., description="Nombre corto para gráficos")
    categoria: str = Field(..., description="Categoría: virus, bacteria, etc.")
    grupo: str = Field(..., description="Grupo: respiratorio, entérico, etc.")
    descripcion: Optional[str] = Field(None, description="Descripción del agente")
    activo: bool = Field(..., description="Si está activo")
    # Estadísticas
    total_eventos: int = Field(0, description="Total de eventos donde se buscó/detectó")
    eventos_positivos: int = Field(0, description="Eventos con resultado positivo")
    eventos_negativos: int = Field(0, description="Eventos con resultado negativo")
    tasa_positividad: float = Field(0.0, description="Tasa de positividad (%)")


class AgentesCategoriasResponse(BaseModel):
    """Respuesta con categorías y grupos de agentes"""
    categorias: List[str] = Field(..., description="Lista de categorías únicas")
    grupos: List[str] = Field(..., description="Lista de grupos únicos")


async def list_agentes(
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(50, ge=1, le=200, description="Elementos por página"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    grupo: Optional[str] = Query(None, description="Filtrar por grupo"),
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    busqueda: Optional[str] = Query(None, description="Buscar por nombre o código"),
    ordenar_por: str = Query(
        "eventos_positivos",
        description="Campo para ordenar: nombre, codigo, total_eventos, eventos_positivos, tasa_positividad"
    ),
    orden: str = Query("desc", description="Orden: asc o desc"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole()),
) -> PaginatedResponse[AgenteEtiologicoInfo]:
    """
    Lista agentes etiológicos con estadísticas de eventos.
    Permite ordenar por cantidad de eventos o tasa de positividad.
    """
    try:
        # Subquery para estadísticas por agente
        stats_subquery = (
            select(
                EventoAgente.id_agente,
                func.count(EventoAgente.id).label("total_eventos"),
                func.sum(
                    case(
                        (EventoAgente.resultado == ResultadoDeteccion.POSITIVO, 1),
                        else_=0
                    )
                ).label("eventos_positivos"),
                func.sum(
                    case(
                        (EventoAgente.resultado == ResultadoDeteccion.NEGATIVO, 1),
                        else_=0
                    )
                ).label("eventos_negativos"),
            )
            .group_by(EventoAgente.id_agente)
            .subquery()
        )

        # Query principal con LEFT JOIN a estadísticas
        query = (
            select(
                AgenteEtiologico,
                func.coalesce(stats_subquery.c.total_eventos, 0).label("total_eventos"),
                func.coalesce(stats_subquery.c.eventos_positivos, 0).label("eventos_positivos"),
                func.coalesce(stats_subquery.c.eventos_negativos, 0).label("eventos_negativos"),
            )
            .outerjoin(stats_subquery, AgenteEtiologico.id == stats_subquery.c.id_agente)
        )

        # Aplicar filtros
        if categoria:
            query = query.where(AgenteEtiologico.categoria == categoria)
        if grupo:
            query = query.where(AgenteEtiologico.grupo == grupo)
        if activo is not None:
            query = query.where(AgenteEtiologico.activo == activo)
        if busqueda:
            search_pattern = f"%{busqueda}%"
            query = query.where(
                (AgenteEtiologico.nombre.ilike(search_pattern)) |
                (AgenteEtiologico.codigo.ilike(search_pattern)) |
                (AgenteEtiologico.nombre_corto.ilike(search_pattern))
            )

        # Ordenamiento
        order_func = desc if orden.lower() == "desc" else asc
        if ordenar_por == "nombre":
            query = query.order_by(order_func(AgenteEtiologico.nombre))
        elif ordenar_por == "codigo":
            query = query.order_by(order_func(AgenteEtiologico.codigo))
        elif ordenar_por == "total_eventos":
            query = query.order_by(order_func(func.coalesce(stats_subquery.c.total_eventos, 0)))
        elif ordenar_por == "eventos_positivos":
            query = query.order_by(order_func(func.coalesce(stats_subquery.c.eventos_positivos, 0)))
        elif ordenar_por == "tasa_positividad":
            # Ordenar por tasa calculada
            query = query.order_by(
                order_func(
                    case(
                        (func.coalesce(stats_subquery.c.total_eventos, 0) > 0,
                         func.coalesce(stats_subquery.c.eventos_positivos, 0) * 100.0 /
                         func.coalesce(stats_subquery.c.total_eventos, 1)),
                        else_=0
                    )
                )
            )
        else:
            # Default: por eventos positivos descendente
            query = query.order_by(desc(func.coalesce(stats_subquery.c.eventos_positivos, 0)))

        # Contar total
        count_query = select(func.count(AgenteEtiologico.id))
        if categoria:
            count_query = count_query.where(AgenteEtiologico.categoria == categoria)
        if grupo:
            count_query = count_query.where(AgenteEtiologico.grupo == grupo)
        if activo is not None:
            count_query = count_query.where(AgenteEtiologico.activo == activo)
        if busqueda:
            search_pattern = f"%{busqueda}%"
            count_query = count_query.where(
                (AgenteEtiologico.nombre.ilike(search_pattern)) |
                (AgenteEtiologico.codigo.ilike(search_pattern)) |
                (AgenteEtiologico.nombre_corto.ilike(search_pattern))
            )

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Paginación
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        # Ejecutar
        result = await db.execute(query)
        rows = result.all()

        # Convertir a modelo de respuesta
        agentes_info = []
        for row in rows:
            agente = row[0]
            total_eventos = row[1] or 0
            eventos_positivos = row[2] or 0
            eventos_negativos = row[3] or 0

            tasa_positividad = 0.0
            if total_eventos > 0:
                tasa_positividad = round((eventos_positivos / total_eventos) * 100, 2)

            agentes_info.append(
                AgenteEtiologicoInfo(
                    id=agente.id,
                    codigo=agente.codigo,
                    nombre=agente.nombre,
                    nombre_corto=agente.nombre_corto,
                    categoria=agente.categoria,
                    grupo=agente.grupo,
                    descripcion=agente.descripcion,
                    activo=agente.activo,
                    total_eventos=total_eventos,
                    eventos_positivos=eventos_positivos,
                    eventos_negativos=eventos_negativos,
                    tasa_positividad=tasa_positividad,
                )
            )

        total_pages = (total + per_page - 1) // per_page if total > 0 else 0

        return PaginatedResponse(
            data=agentes_info,
            meta=PaginationMeta(
                page=page,
                page_size=per_page,
                total=total,
                total_pages=total_pages,
            ),
            links={
                "first": f"/api/v1/agentes?page=1&per_page={per_page}" if total_pages > 0 else None,
                "prev": f"/api/v1/agentes?page={page-1}&per_page={per_page}" if page > 1 else None,
                "next": f"/api/v1/agentes?page={page+1}&per_page={per_page}" if page < total_pages else None,
                "last": f"/api/v1/agentes?page={total_pages}&per_page={per_page}" if total_pages > 0 else None,
            },
        )
    except Exception as e:
        logger.error(f"Error listando agentes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo agentes: {str(e)}",
        )


async def get_agentes_categorias(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(RequireAnyRole()),
) -> AgentesCategoriasResponse:
    """Obtiene las categorías y grupos únicos de agentes"""
    try:
        # Categorías únicas
        cat_result = await db.execute(
            select(AgenteEtiologico.categoria).distinct().order_by(AgenteEtiologico.categoria)
        )
        categorias = [row[0] for row in cat_result.all()]

        # Grupos únicos
        grupo_result = await db.execute(
            select(AgenteEtiologico.grupo).distinct().order_by(AgenteEtiologico.grupo)
        )
        grupos = [row[0] for row in grupo_result.all()]

        return AgentesCategoriasResponse(
            categorias=categorias,
            grupos=grupos,
        )
    except Exception as e:
        logger.error(f"Error obteniendo categorías: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo categorías: {str(e)}",
        )

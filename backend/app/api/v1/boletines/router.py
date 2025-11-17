"""
Router para endpoints de boletines epidemiológicos
"""

from typing import List

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse

from app.api.v1.boletines import instances_crud, templates_crud
from app.api.v1.boletines.schemas import (
    BoletinGenerateRequest,
    BoletinInstanceResponse,
    BoletinTemplateCreate,
    BoletinTemplateResponse,
    BoletinTemplateUpdate,
)
from app.core.schemas.response import ErrorResponse, SuccessResponse

router = APIRouter(prefix="/boletines", tags=["Boletines"])


# ============================================================================
# Templates Endpoints
# ============================================================================

router.add_api_route(
    "/templates",
    templates_crud.create_template,
    methods=["POST"],
    response_model=SuccessResponse[BoletinTemplateResponse],
    name="create_boletin_template",
    summary="Crear template de boletín",
    responses={
        400: {"model": ErrorResponse, "description": "Datos inválidos"},
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)

router.add_api_route(
    "/templates",
    templates_crud.list_templates,
    methods=["GET"],
    response_model=SuccessResponse[List[BoletinTemplateResponse]],
    name="list_boletin_templates",
    summary="Listar templates de boletines",
    responses={
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)

router.add_api_route(
    "/templates/{template_id}",
    templates_crud.get_template,
    methods=["GET"],
    response_model=SuccessResponse[BoletinTemplateResponse],
    name="get_boletin_template",
    summary="Obtener template por ID",
    responses={
        404: {"model": ErrorResponse, "description": "Template no encontrado"},
        403: {"model": ErrorResponse, "description": "Sin permisos"},
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)

router.add_api_route(
    "/templates/{template_id}",
    templates_crud.update_template,
    methods=["PUT"],
    response_model=SuccessResponse[BoletinTemplateResponse],
    name="update_boletin_template",
    summary="Actualizar template",
    responses={
        404: {"model": ErrorResponse, "description": "Template no encontrado"},
        403: {"model": ErrorResponse, "description": "Sin permisos"},
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)

router.add_api_route(
    "/templates/{template_id}",
    templates_crud.delete_template,
    methods=["DELETE"],
    response_model=SuccessResponse[dict],
    name="delete_boletin_template",
    summary="Eliminar template",
    responses={
        404: {"model": ErrorResponse, "description": "Template no encontrado"},
        403: {"model": ErrorResponse, "description": "Sin permisos"},
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)

router.add_api_route(
    "/templates/{template_id}/duplicate",
    templates_crud.duplicate_template,
    methods=["POST"],
    response_model=SuccessResponse[BoletinTemplateResponse],
    name="duplicate_boletin_template",
    summary="Duplicar template",
    responses={
        404: {"model": ErrorResponse, "description": "Template no encontrado"},
        403: {"model": ErrorResponse, "description": "Sin permisos"},
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)


# ============================================================================
# Instances Endpoints
# ============================================================================

router.add_api_route(
    "/instances",
    instances_crud.create_instance,
    methods=["POST"],
    response_model=SuccessResponse[BoletinInstanceResponse],
    name="create_boletin_instance",
    summary="Crear instancia de boletín",
    description="Crea una instancia pendiente. El PDF se genera en un paso posterior.",
    responses={
        404: {"model": ErrorResponse, "description": "Template no encontrado"},
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)

router.add_api_route(
    "/instances",
    instances_crud.list_instances,
    methods=["GET"],
    response_model=SuccessResponse[List[BoletinInstanceResponse]],
    name="list_boletin_instances",
    summary="Listar instancias de boletines",
    responses={
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)

router.add_api_route(
    "/instances/{instance_id}",
    instances_crud.get_instance,
    methods=["GET"],
    response_model=SuccessResponse[BoletinInstanceResponse],
    name="get_boletin_instance",
    summary="Obtener instancia por ID",
    responses={
        404: {"model": ErrorResponse, "description": "Instancia no encontrada"},
        403: {"model": ErrorResponse, "description": "Sin permisos"},
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)

router.add_api_route(
    "/instances/{instance_id}",
    instances_crud.delete_instance,
    methods=["DELETE"],
    response_model=SuccessResponse[dict],
    name="delete_boletin_instance",
    summary="Eliminar instancia",
    responses={
        404: {"model": ErrorResponse, "description": "Instancia no encontrada"},
        403: {"model": ErrorResponse, "description": "Sin permisos"},
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)


# TODO: Agregar endpoints para:
# - POST /instances/{instance_id}/generate-pdf (generar PDF de instancia)
# - GET /instances/{instance_id}/download (descargar PDF)
# - GET /instances/{instance_id}/preview (preview HTML)

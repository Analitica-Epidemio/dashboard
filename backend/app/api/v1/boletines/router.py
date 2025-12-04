"""
Router para endpoints de boletines epidemiológicos
"""

from typing import List

from fastapi import APIRouter

from app.api.v1.boletines import instances_crud, templates_crud
from app.api.v1.boletines.generate_draft import generate_draft
from app.api.v1.boletines.schemas import (
    BoletinInstanceResponse,
    BoletinTemplateResponse,
    GenerateDraftResponse,
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

router.add_api_route(
    "/instances/{instance_id}/content",
    instances_crud.update_instance_content,
    methods=["PUT"],
    response_model=SuccessResponse[BoletinInstanceResponse],
    name="update_boletin_instance_content",
    summary="Actualizar contenido de instancia",
    responses={
        404: {"model": ErrorResponse, "description": "Instancia no encontrada"},
        403: {"model": ErrorResponse, "description": "Sin permisos"},
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)

router.add_api_route(
    "/instances/{instance_id}/export-pdf",
    instances_crud.generate_instance_pdf,
    methods=["POST"],
    name="generate_boletin_instance_pdf",
    summary="Generar y descargar PDF de instancia",
    responses={
        404: {"model": ErrorResponse, "description": "Instancia no encontrada"},
        403: {"model": ErrorResponse, "description": "Sin permisos"},
        400: {"model": ErrorResponse, "description": "Sin contenido para generar"},
        500: {"model": ErrorResponse, "description": "Error generando PDF"},
    },
)


# ============================================================================
# New automatic generation endpoint
# ============================================================================

router.add_api_route(
    "/generate-draft",
    generate_draft,
    methods=["POST"],
    response_model=SuccessResponse[GenerateDraftResponse],
    name="generate_draft_boletin",
    summary="Generar borrador de boletín automático basado en analytics",
    description="Genera un boletín epidemiológico automático usando datos de analytics y snippets",
    responses={
        400: {"model": ErrorResponse, "description": "Datos inválidos"},
        500: {"model": ErrorResponse, "description": "Error interno"},
    },
)


# TODO: Agregar endpoints para:
# - POST /instances/{instance_id}/generate-pdf (generar PDF de instancia)
# - GET /instances/{instance_id}/download (descargar PDF)
# - GET /instances/{instance_id}/preview (preview HTML)

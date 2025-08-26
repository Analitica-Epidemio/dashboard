"""
Endpoint simplificado para upload de hojas Excel individuales.

Arquitectura optimizada:
- Cliente maneja preview
- Solo sube la hoja seleccionada
- Procesamiento directo en backend
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from fastapi.responses import JSONResponse
from app.core.schemas.response import SuccessResponse, ErrorResponse, ErrorDetail
from app.domains.uploads.services import sheet_service
from app.domains.uploads.schemas import SheetUploadResponse

router = APIRouter(prefix="/uploads", tags=["Uploads"])


@router.post(
    "/sheet",
    responses={
        200: {
            "model": SuccessResponse[SheetUploadResponse],
            "description": "Hoja Excel procesada exitosamente"
        },
        400: {
            "model": ErrorResponse,
            "description": "Archivo no válido o formato incorrecto"
        },
        413: {
            "model": ErrorResponse, 
            "description": "Archivo muy grande (máx 50MB)"
        },
        422: {
            "model": ErrorResponse,
            "description": "Error al procesar hoja Excel"
        }
    }
)
async def upload_sheet(
    file: UploadFile = File(..., description="Archivo Excel con una sola hoja"),
    original_filename: str = Form(..., description="Nombre del archivo original"),
    sheet_name: str = Form(..., description="Nombre de la hoja que se está subiendo"),
):
    """
    Sube y procesa una hoja específica de Excel.
    
    **Flujo optimizado:**
    1. Cliente selecciona archivo y hace preview local
    2. Usuario selecciona hoja  
    3. Cliente extrae solo esa hoja y la sube aquí
    4. Backend procesa directamente la hoja
    
    **Ventajas:**
    - Menos ancho de banda (solo la hoja necesaria)
    - Procesamiento más rápido
    - Mejor experiencia de usuario
    
    **Parámetros:**
    - **file**: Archivo Excel que contiene solo la hoja seleccionada
    - **original_filename**: Nombre del archivo original completo
    - **sheet_name**: Nombre de la hoja que se procesó
    """
    
    try:
        # Procesar upload de la hoja
        result = sheet_service.process_sheet_upload(
            file=file,
            original_filename=original_filename,
            sheet_name=sheet_name
        )
        
        # Respuesta exitosa
        success_response = SuccessResponse(data=result)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=success_response.model_dump(mode="json")
        )
        
    except HTTPException as e:
        # Errores controlados del servicio
        error_code_map = {
            400: "INVALID_FILE",
            413: "FILE_TOO_LARGE", 
            422: "EXCEL_PROCESSING_ERROR",
            500: "INTERNAL_SERVER_ERROR"
        }
        
        error_response = ErrorResponse(
            error=ErrorDetail(
                code=error_code_map.get(e.status_code, "UNKNOWN_ERROR"),
                message=e.detail,
                field="file"
            )
        )
        
        return JSONResponse(
            status_code=e.status_code,
            content=error_response.model_dump()
        )
        
    except Exception as e:
        # Errores no controlados
        error_response = ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="Error interno del servidor",
                field=None
            )
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump()
        )
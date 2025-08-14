# -*- coding: utf-8 -*-
"""Schemas para respuestas de error"""
from pydantic import BaseModel
from typing import Optional, Any, List


class ErrorResponse(BaseModel):
    """Modelo estándar para respuestas de error"""
    error: bool = True
    message: str
    status_code: int
    path: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": True,
                "message": "Recurso no encontrado",
                "status_code": 404,
                "path": "/api/v1/resource/123"
            }
        }


class ValidationErrorResponse(ErrorResponse):
    """Modelo para errores de validación con detalles"""
    details: Optional[List[Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": True,
                "message": "Error de validación en los datos enviados",
                "status_code": 422,
                "path": "/api/v1/resource",
                "details": [
                    {
                        "loc": ["body", "field"],
                        "msg": "field required",
                        "type": "value_error.missing"
                    }
                ]
            }
        }
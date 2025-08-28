"""Middleware personalizado para manejo de excepciones y otros aspectos transversales."""

import time
import traceback
from typing import Any, Callable
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    BusinessRuleException,
    DatabaseException,
    DuplicateException,
    EpidemiologiaException,
    ExternalServiceException,
    NotFoundException,
    ValidationException,
)
from app.core.schemas.response import ErrorDetail, ErrorResponse


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware para manejo centralizado de excepciones."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Any]
    ) -> Response:
        """Procesa la request y maneja excepciones."""
        # Generar ID único para tracking
        request_id = str(uuid4())
        request.state.request_id = request_id

        try:
            response: Response = await call_next(request)
            return response

        except EpidemiologiaException as e:
            return await self._handle_epidemiologia_exception(e, request_id)
        except HTTPException as e:
            return await self._handle_http_exception(e, request_id)
        except Exception as e:
            return await self._handle_generic_exception(e, request_id)

    async def _handle_epidemiologia_exception(
        self, exc: EpidemiologiaException, request_id: str
    ) -> JSONResponse:
        """Maneja excepciones específicas del dominio."""
        status_code = self._get_status_code_for_exception(exc)

        error_detail = ErrorDetail(
            code=exc.error_code or "UNKNOWN_ERROR", message=exc.message, field=None
        )

        response = ErrorResponse(error=error_detail, request_id=request_id)

        return JSONResponse(status_code=status_code, content=response.model_dump())

    async def _handle_http_exception(
        self, exc: HTTPException, request_id: str
    ) -> JSONResponse:
        """Maneja excepciones HTTP.

        Si es una excepción estructurada (con code), la usa.
        Si no, es la red de seguridad para excepciones no estructuradas.
        """
        # Red de seguridad para HTTPException de FastAPI o librerías externas
        # En nuestro código NO deberíamos llegar aquí nunca
        error_detail = ErrorDetail(
            code=f"HTTP_{exc.status_code}",
            message=str(exc.detail) if exc.detail else f"Error HTTP {exc.status_code}",
            field=None,
        )

        # Log para identificar dónde se están usando excepciones (no deberíamos)
        print(
            f"[WARNING] HTTPException detectada - deberíamos usar JSONResponse: {exc.detail}"
        )

        response = ErrorResponse(error=error_detail, request_id=request_id)

        return JSONResponse(status_code=exc.status_code, content=response.model_dump())

    async def _handle_generic_exception(
        self, exc: Exception, request_id: str
    ) -> JSONResponse:
        """Red de seguridad para excepciones no esperadas.

        Esto SOLO debería ocurrir con bugs reales.
        En producción, no exponer detalles del error.
        """
        # Log completo para debugging
        error_traceback = traceback.format_exc()
        print(f"[ERROR] Excepción no manejada [{request_id}]: {error_traceback}")

        error_detail = ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="Se produjo un error interno. Por favor, intente nuevamente.",
            field=None,
        )

        response = ErrorResponse(error=error_detail, request_id=request_id)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response.model_dump(),
        )

    def _get_status_code_for_exception(self, exc: EpidemiologiaException) -> int:
        """Mapea tipos de excepción a códigos HTTP."""
        if isinstance(exc, ValidationException):
            return status.HTTP_422_UNPROCESSABLE_ENTITY
        elif isinstance(exc, BusinessRuleException):
            return status.HTTP_400_BAD_REQUEST
        elif isinstance(exc, NotFoundException):
            return status.HTTP_404_NOT_FOUND
        elif isinstance(exc, DuplicateException):
            return status.HTTP_409_CONFLICT
        elif isinstance(exc, AuthenticationException):
            return status.HTTP_401_UNAUTHORIZED
        elif isinstance(exc, AuthorizationException):
            return status.HTTP_403_FORBIDDEN
        elif isinstance(exc, ExternalServiceException):
            return status.HTTP_502_BAD_GATEWAY
        elif isinstance(exc, DatabaseException):
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        else:
            return status.HTTP_500_INTERNAL_SERVER_ERROR


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging de requests."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Any]
    ) -> Response:
        """Procesa la request y registra información."""
        start_time = time.time()

        # Log básico de la request
        method = request.method
        url = str(request.url)
        request_id = getattr(request.state, "request_id", "unknown")

        print(f"[{request_id}] {method} {url} - Started")

        # Procesar request
        response: Response = await call_next(request)

        # Log de la response
        process_time = time.time() - start_time
        status_code = response.status_code

        print(f"[{request_id}] {method} {url} - {status_code} - {process_time:.3f}s")

        # Agregar headers de response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)

        return response


def setup_middleware(app: FastAPI) -> None:
    """Configura todos los middlewares de la aplicación."""

    # Middleware de logging (debe ir antes del manejo de excepciones)
    app.add_middleware(RequestLoggingMiddleware)

    # Middleware de manejo de excepciones
    app.add_middleware(ExceptionHandlerMiddleware)


# Handler personalizado para excepciones de validación de Pydantic
async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Maneja excepciones de validación de Pydantic."""
    request_id = getattr(request.state, "request_id", str(uuid4()))

    errors = []
    if hasattr(exc, "errors"):
        for error in exc.errors():
            error_detail = ErrorDetail(
                code="VALIDATION_ERROR",
                message=error.get("msg", "Error de validación"),
                field=".".join(str(loc) for loc in error.get("loc", [])),
                details=error,
            )
            errors.append(error_detail.model_dump())
    else:
        error_detail = ErrorDetail(
            code="VALIDATION_ERROR", message=str(exc), field=None, details=None
        )
        errors.append(error_detail.model_dump())

    response: StandardResponse[Any] = StandardResponse.error_response(
        message="Error de validación en los datos proporcionados", errors=errors
    )

    response_dict = response.model_dump()
    response_dict["request_id"] = request_id
    response_dict["timestamp"] = time.time()

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=response_dict
    )

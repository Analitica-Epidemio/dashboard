"""Excepciones personalizadas del sistema."""

from typing import Any, Dict, Optional


class EpidemiologiaException(Exception):
    """Excepción base del sistema."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
    ):
        self.message = message
        self.details = details or {}
        self.error_code = error_code
        super().__init__(self.message)


class ValidationException(EpidemiologiaException):
    """Excepción de validación de datos."""

    def __init__(
        self,
        message: str = "Error de validación",
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        details = {"field": field, "value": value} if field else {}
        super().__init__(message, details, "VALIDATION_ERROR", **kwargs)


class BusinessRuleException(EpidemiologiaException):
    """Excepción de reglas de negocio."""

    def __init__(self, message: str, rule: Optional[str] = None, **kwargs: Any) -> None:
        details = {"rule": rule} if rule else {}
        super().__init__(message, details, "BUSINESS_RULE_ERROR", **kwargs)


class NotFoundException(EpidemiologiaException):
    """Excepción cuando no se encuentra un recurso."""

    def __init__(
        self, resource: str, identifier: Optional[str] = None, **kwargs: Any
    ) -> None:
        message = f"{resource} no encontrado"
        if identifier:
            message += f" con ID: {identifier}"

        details = {"resource": resource, "identifier": identifier}
        super().__init__(message, details, "NOT_FOUND_ERROR", **kwargs)


class DuplicateException(EpidemiologiaException):
    """Excepción cuando se intenta crear un recurso duplicado."""

    def __init__(self, resource: str, field: str, value: str, **kwargs: Any) -> None:
        message = f"{resource} ya existe con {field}: {value}"
        details = {"resource": resource, "field": field, "value": value}
        super().__init__(message, details, "DUPLICATE_ERROR", **kwargs)


class AuthenticationException(EpidemiologiaException):
    """Excepción de autenticación."""

    def __init__(self, message: str = "Error de autenticación", **kwargs: Any) -> None:
        super().__init__(message, error_code="AUTH_ERROR", **kwargs)


class AuthorizationException(EpidemiologiaException):
    """Excepción de autorización."""

    def __init__(
        self,
        message: str = "No tienes permisos para realizar esta acción",
        required_permission: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        details = (
            {"required_permission": required_permission} if required_permission else {}
        )
        super().__init__(message, details, "AUTHORIZATION_ERROR", **kwargs)


class ExternalServiceException(EpidemiologiaException):
    """Excepción de servicios externos."""

    def __init__(
        self,
        service: str,
        message: str = "Error en servicio externo",
        status_code: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        details = {"service": service, "status_code": status_code}
        super().__init__(message, details, "EXTERNAL_SERVICE_ERROR", **kwargs)


class DatabaseException(EpidemiologiaException):
    """Excepción de base de datos."""

    def __init__(
        self,
        message: str = "Error de base de datos",
        operation: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        details = {"operation": operation} if operation else {}
        super().__init__(message, details, "DATABASE_ERROR", **kwargs)

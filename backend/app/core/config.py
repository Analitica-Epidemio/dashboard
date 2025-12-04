"""Configuración de la aplicación."""

from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración centralizada usando variables de entorno."""

    # =============================================================================
    # CONFIGURACIÓN DE PROYECTO
    # =============================================================================
    PROJECT_NAME: str = "Sistema de Epidemiología"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"

    # =============================================================================
    # CONFIGURACIÓN DE ENTORNO
    # =============================================================================
    ENVIRONMENT: str = "development"
    # SEGURIDAD: DEBUG=False por defecto. Solo habilitar explícitamente en .env
    DEBUG: bool = False

    # =============================================================================
    # CONFIGURACIÓN DE BASE DE DATOS
    # =============================================================================
    # IMPORTANTE: Usar credenciales fuertes en producción
    DATABASE_URL: str

    # =============================================================================
    # CONFIGURACIÓN DE SEGURIDAD
    # =============================================================================
    # CRÍTICO: Esta clave debe ser generada con: openssl rand -hex 32
    # NUNCA usar un valor por defecto en producción
    SECRET_KEY: str  # Sin valor por defecto - DEBE estar en .env
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 horas
    ALLOWED_HOSTS: str = "localhost,127.0.0.1,0.0.0.0"

    # =============================================================================
    # CONFIGURACIÓN DE CORS
    # =============================================================================
    CORS_ORIGINS: str = (
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000"
    )

    @property
    def BACKEND_CORS_ORIGINS(self) -> List[str]:
        """Convierte CORS_ORIGINS en lista."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # =============================================================================
    # CONFIGURACIÓN DE REDIS Y CELERY
    # =============================================================================
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # =============================================================================
    # CONFIGURACIÓN DE ARCHIVOS
    # =============================================================================
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 52428800  # 50MB
    SOURCES_FOLDER: str = "./sources"
    PROCESSED_FILES_FOLDER: str = "./processed"

    # =============================================================================
    # CONFIGURACIÓN DE EMAIL
    # =============================================================================
    MAIL_USERNAME: str = "tu_email@ejemplo.com"
    MAIL_PASSWORD: str = "tu_password_de_email"
    MAIL_FROM: str = "noreply@epidemiologia.gob.ar"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_FROM_NAME: str = "Sistema de Epidemiología"
    FRONTEND_URL: str = "http://localhost:3000"

    # =============================================================================
    # CONFIGURACIÓN DE LOGGING
    # =============================================================================
    LOG_LEVEL: str = "INFO"

    # =============================================================================
    # CONFIGURACIÓN ESPECÍFICA DE EPIDEMIOLOGÍA
    # =============================================================================
    DEFAULT_TIMEZONE: str = "America/Argentina/Buenos_Aires"
    PAGINATION_PAGE_SIZE: int = 50
    PAGINATION_MAX_PAGE_SIZE: int = 200

    # =============================================================================
    # CONFIGURACIÓN DE GEOCODIFICACIÓN
    # =============================================================================
    ENABLE_GEOCODING: bool = False

    # Proveedor de geocodificación: "mapbox" o "google"
    GEOCODING_PROVIDER: str = "google"  # Cambiar a "mapbox" para usar Mapbox

    # API Keys (solo se usa la del proveedor activo)
    MAPBOX_ACCESS_TOKEN: str = ""  # Para provider "mapbox"
    GOOGLE_MAPS_API_KEY: str = ""  # Para provider "google"

    # Configuración general
    GEOCODING_RATE_LIMIT: int = 600
    GEOCODING_TIMEOUT: int = 5

    # =============================================================================
    # CONFIGURACIÓN DE DESARROLLO
    # =============================================================================
    ENABLE_DOCS: bool = True
    ENABLE_REDOC: bool = True
    ENABLE_OPENAPI: bool = True

    @property
    def BASE_DIR(self) -> Path:
        """Retorna el directorio base del proyecto."""
        return Path(__file__).resolve().parent.parent

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignorar variables de entorno extra (ej: DB_NAME, DB_USER, etc.)


settings = Settings()


def get_settings() -> Settings:
    """Obtiene la configuración de la aplicación."""
    return settings

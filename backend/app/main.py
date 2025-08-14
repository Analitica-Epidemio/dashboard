"""
Aplicación principal FastAPI para el Sistema de Epidemiología Moderna.

Sistema de vigilancia epidemiológica con procesamiento ETL, autenticación
JWT y gestión de eventos de salud pública.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Callable, Dict

import uvicorn
from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import create_db_and_tables
from app.core.middleware import setup_middleware

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Maneja el ciclo de vida de la aplicación.

    Se ejecuta al iniciar y cerrar la aplicación.
    """
    # Startup
    logger.info("🚀 Iniciando Sistema de Epidemiología Moderna...")

    # Intentar crear tablas de base de datos (opcional en desarrollo)
    try:
        create_db_and_tables()
        logger.info("✅ Base de datos inicializada")
    except Exception as e:
        logger.warning(f"⚠️ No se pudo inicializar la base de datos: {e}")
        logger.info("ℹ️ La aplicación continuará sin base de datos")

    logger.info("🏥 Sistema de Epidemiología listo para recibir requests")

    yield

    # Shutdown
    logger.info("🔄 Cerrando Sistema de Epidemiología...")


def create_application() -> FastAPI:
    """
    Factory para crear la aplicación FastAPI.

    Returns:
        Aplicación FastAPI configurada
    """
    app = FastAPI(
        title="Sistema de Epidemiología Moderna",
        description="""
        Sistema integral de vigilancia epidemiológica para instituciones de salud pública.
        """,
        version="1.0.0",
        contact={
            "name": "Equipo de Desarrollo Epidemiología",
        },
        lifespan=lifespan,
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
    )

    # Configurar middleware personalizado
    setup_middleware(app)

    # Configurar middleware estándar
    setup_standard_middleware(app)

    # Configurar exception handlers
    setup_exception_handlers(app)

    # Incluir routers
    app.include_router(api_router)

    return app


def setup_standard_middleware(app: FastAPI) -> None:
    """
    Configura middleware de la aplicación.

    Args:
        app: Instancia de FastAPI
    """
    # CORS - Configurado según el entorno
    if settings.ENVIRONMENT == "development":
        # En desarrollo, permitir cualquier origen localhost
        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            allow_headers=["*"],
        )
        logger.info(
            "🌐 CORS configurado para desarrollo - permitiendo cualquier puerto en localhost"
        )
    elif settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.BACKEND_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            allow_headers=["*"],
        )

    # Trusted hosts para seguridad en producción
    if settings.ALLOWED_HOSTS:
        allowed_hosts = [host.strip() for host in settings.ALLOWED_HOSTS.split(",")]
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

    # Middleware personalizado para logging de requests
    @app.middleware("http")
    async def log_requests(
        request: Request, call_next: Callable[[Request], Any]
    ) -> Response:
        """Log de requests entrantes"""
        start_time = time.time()

        logger.info(
            f"🔍 {request.method} {request.url.path} - "
            f"IP: {request.client.host if request.client else 'unknown'}"
        )

        response = await call_next(request)

        process_time = time.time() - start_time
        logger.info(
            f"✅ {request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )

        return response  # type: ignore[no-any-return]


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Configura manejadores de excepciones personalizados.

    Args:
        app: Instancia de FastAPI
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """Maneja excepciones HTTP con formato consistente"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "message": exc.detail,
                "status_code": exc.status_code,
                "path": str(request.url.path),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": True,
                "message": "Error de validación en los datos enviados",
                "status_code": 422,
                "path": str(request.url.path),
                "details": exc.errors(),
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Maneja excepciones generales no capturadas"""
        logger.error(f"💥 Error no manejado: {str(exc)}", exc_info=True)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": True,
                "message": "Error interno del servidor"
                if settings.ENVIRONMENT == "production"
                else str(exc),
                "status_code": 500,
                "path": str(request.url.path),
            },
        )


# Crear la aplicación
app = create_application()


@app.get("/", include_in_schema=False)
async def root() -> Dict[str, Any]:
    """Endpoint raíz con información del sistema"""
    return {
        "message": "🏥 Sistema de Epidemiología Moderna",
        "version": "1.0.0",
        "status": "operational",
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs" if settings.ENVIRONMENT != "production" else None,
    }


@app.get("/health", include_in_schema=False)
async def health_check() -> Dict[str, Any]:
    """Health check para monitoreo"""
    from sqlalchemy import text

    from app.core.database import engine

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Error en health check de BD: {e}")
        db_status = "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "timestamp": time.time(),
        "services": {
            "database": db_status,
        },
        "version": "1.0.0",
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False,
        log_level="info",
        access_log=True,
    )

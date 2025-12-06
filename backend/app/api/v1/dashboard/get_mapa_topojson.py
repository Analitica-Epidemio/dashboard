"""
Endpoint para servir datos geoespaciales TopoJSON con optimizaciones
- Compresión gzip automática
- Cuantización de coordenadas
- Caché HTTP optimizado
- Lazy loading por nivel geográfico
"""

import logging

from fastapi import Query, Response

from app.core.config import settings
from app.domains.territorio.utils.topojson_optimizer import TopoJSONOptimizer

logger = logging.getLogger(__name__)

# Inicializar optimizador con ruta de archivos TopoJSON
TOPOJSON_DIR = settings.BASE_DIR / "data" / "topojson"
optimizer = TopoJSONOptimizer(str(TOPOJSON_DIR))


async def get_topojson_data(
    nivel: str = Query(
        ...,
        description="Nivel geográfico: 'departamentos' (default), o nombre de provincia en minúsculas",
        regex="^[a-z_]+$",
    ),
    compress: bool = Query(
        True,
        description="Aplicar compresión gzip",
    ),
    quantize: bool = Query(
        True,
        description="Cuantizar coordenadas para reducir tamaño",
    ),
    quantize_decimals: int = Query(
        4,
        description="Decimal places for coordinate precision (4 = ~11m accuracy for Argentina)",
        ge=0,
        le=6,
    ),
) -> Response:
    """
    Servir datos TopoJSON optimizados para mapas interactivos.

    Optimizaciones aplicadas:
    - Compresión gzip: reduce ~89% del tamaño (3.9MB → ~400KB)
    - Cuantización: reduce ~30-50% adicional sin impacto visual
    - Caché HTTP: agresivo con ETag y Cache-Control
    - Lazy loading: cargar solo el nivel geográfico necesario

    ## Ejemplos de uso:
    - `/api/v1/dashboard/mapa/topojson?nivel=departamentos` - Todos los departamentos
    - `/api/v1/dashboard/mapa/topojson?nivel=buenos_aires` - Solo Buenos Aires
    - `/api/v1/dashboard/mapa/topojson?nivel=departamentos&compress=false` - Sin comprimir
    """

    filename = ""
    try:
        # Construir nombre de archivo
        # "departamentos" → departamentos-argentina.topojson
        # "buenos_aires" → departamentos-buenos_aires.topojson
        if nivel == "departamentos":
            filename = "departamentos-argentina.topojson"
        else:
            filename = f"departamentos-{nivel}.topojson"

        logger.info(
            f"Serving TopoJSON: {filename} "
            f"(compress={compress}, quantize={quantize}, decimals={quantize_decimals})"
        )

        # Cargar y optimizar
        data, content_type = optimizer.load_topojson(
            filename,
            compress=compress,
            quantize=quantize,
            quantize_decimals=quantize_decimals,
        )

        # Preparar headers de respuesta
        headers = {
            "Content-Type": content_type,
            "Content-Length": str(len(data)),
            # Caché agresivo: 7 días para datos estáticos geográficos
            "Cache-Control": "public, max-age=604800, immutable",
            # ETag para validación eficiente
            "ETag": f'"{hash(data)}"',
            # Vary por parámetros que afectan el contenido
            "Vary": "Accept-Encoding",
        }

        if compress:
            headers["Content-Encoding"] = "gzip"

        logger.info(
            f"TopoJSON served: {len(data)} bytes (compressed={len(data) < 1_000_000})"
        )

        return Response(
            content=data,
            media_type=content_type,
            headers=headers,
        )

    except FileNotFoundError as e:
        logger.warning(f"TopoJSON file not found: {e}")
        available_files = optimizer.get_available_files()
        return Response(
            content=f"TopoJSON file not found: {filename}\n"
            f"Available files: {available_files}",
            status_code=404,
            media_type="text/plain",
        )

    except Exception as e:
        logger.error(f"Error serving TopoJSON: {e}", exc_info=True)
        return Response(
            content=f"Error serving TopoJSON: {str(e)}",
            status_code=500,
            media_type="text/plain",
        )


async def get_topojson_info() -> dict:
    """
    Obtener información sobre archivos TopoJSON disponibles y estadísticas de compresión.

    Útil para debugging y optimización.
    """
    try:
        available_files = optimizer.get_available_files()
        file_infos = []
        compression_stats = []

        for filename in available_files:
            try:
                info = optimizer.get_file_info(filename)
                file_infos.append(info)

                compression = optimizer.estimate_compression(filename)
                compression_stats.append(compression)
            except Exception as e:
                logger.warning(f"Error getting info for {filename}: {e}")

        return {
            "status": "success",
            "available_files": available_files,
            "file_info": file_infos,
            "compression_stats": compression_stats,
        }

    except Exception as e:
        logger.error(f"Error getting TopoJSON info: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
        }

"""
Endpoint para obtener el mapeo de departamentos con IDs INDEC para el frontend.
Esto es lo que usa el mapa para colorear departamentos según eventos.

Retorna un JSON con claves normalizadas que matchean con los nombres del TopoJSON.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


def normalize_name(name: str) -> str:
    """Normalizar nombres para matching con TopoJSON"""
    return (
        name.upper()
        .strip()
        .replace(" ", "_")
        .replace("Á", "A")
        .replace("É", "E")
        .replace("Í", "I")
        .replace("Ó", "O")
        .replace("Ú", "U")
    )


async def get_departamentos_mapping() -> Dict[str, Any]:
    """
    Obtener mapeo de todos los departamentos con IDs INDEC.

    Este mapeo es usado por el frontend para:
    - Matchear features de TopoJSON con datos de la API
    - Agregar IDs INDEC a features geográficas
    - Colorear departamentos en el mapa según eventos

    Format de retorno:
    {
      "PROVINCIA_DEPARTAMENTO": {
        "provincia": "string",
        "departamento": "string",
        "id_provincia_indec": number,
        "id_departamento_indec": number
      }
    }

    Se carga desde el archivo JSON pre-generado que está sincronizado con el TopoJSON.
    """

    try:
        # Usar el archivo departamentos_ids.json generado previamente
        # Este archivo está en el frontend
        # Intenta múltiples rutas posibles
        possible_paths = [
            # Ruta relativa desde backend root
            Path(__file__).resolve().parent.parent.parent.parent.parent
            / "frontend"
            / "src"
            / "app"
            / "dashboard"
            / "mapa"
            / "_components"
            / "departamentos_ids.json",
            # Ruta absoluta
            Path("/Users/ignacio/Documents/work/epidemiologia/dashboard/frontend/src/app/dashboard/mapa/_components/departamentos_ids.json"),
        ]

        for mapping_path in possible_paths:
            logger.debug(f"Checking mapping file at: {mapping_path}")
            if mapping_path.exists():
                logger.info(f"Loading mapping from {mapping_path}")
                with open(mapping_path, "r", encoding="utf-8") as f:
                    mapping = json.load(f)
                logger.info(f"Loaded mapping with {len(mapping)} entries from file")
                return mapping

        logger.warning(f"Mapping file not found. Tried: {possible_paths}")
        return {}

    except Exception as e:
        logger.error(f"Error loading departamentos mapping: {e}", exc_info=True)
        # Fallback: return empty dict instead of raising to avoid 500 error
        return {}

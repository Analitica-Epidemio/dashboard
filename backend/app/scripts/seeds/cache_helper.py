"""
Helper para cachear descargas de WFS/API externas.

Guarda las respuestas en archivos locales para acelerar re-ejecuciones
y proveer fallback cuando los servicios están caídos.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import cast

# Directorio de caché (en .cache/seeds/ en la raíz del proyecto)
# Esto mantiene el cache fuera de app/ para builds de Docker más rápidos
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent  # backend/
CACHE_DIR = _PROJECT_ROOT / ".cache" / "seeds"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_cached_response(cache_key: str, max_age_days: int = 7) -> str | None:
    """
    Obtiene respuesta cacheada si existe y no está muy vieja.

    Args:
        cache_key: Nombre del archivo de caché (sin extensión)
        max_age_days: Máxima edad del caché en días (default: 7)

    Returns:
        Contenido del caché o None si no existe/expiró
    """
    cache_file = CACHE_DIR / f"{cache_key}.cache"

    if not cache_file.exists():
        return None

    # Verificar edad del archivo
    file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
    if file_age > timedelta(days=max_age_days):
        print(f"   ⚠️  Caché expirado (antigüedad: {file_age.days} días)")
        return None

    print(f"   ✅ Usando caché local (antigüedad: {file_age.days} días)")
    return cache_file.read_text(encoding="utf-8")


def save_to_cache(cache_key: str, content: str) -> None:
    """
    Guarda contenido en caché.

    Args:
        cache_key: Nombre del archivo de caché (sin extensión)
        content: Contenido a guardar
    """
    cache_file = CACHE_DIR / f"{cache_key}.cache"
    cache_file.write_text(content, encoding="utf-8")

    # Guardar metadata
    metadata_file = CACHE_DIR / f"{cache_key}.meta.json"
    metadata = {
        "cached_at": datetime.now().isoformat(),
        "size_bytes": len(content),
    }
    metadata_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"   💾 Guardado en caché: {len(content):,} bytes")


def download_with_cache(
    url: str,
    cache_key: str,
    max_age_days: int = 7,
    timeout: int = 300,
    verify_ssl: bool = True,
) -> str:
    """
    Descarga desde URL con caché automático.

    Args:
        url: URL a descargar
        cache_key: Nombre del archivo de caché
        max_age_days: Máxima edad del caché en días
        timeout: Timeout de la request en segundos
        verify_ssl: Verificar certificado SSL

    Returns:
        Contenido descargado (desde caché o URL)
    """
    import requests

    # Intentar caché primero
    cached = get_cached_response(cache_key, max_age_days)
    if cached:
        return cached

    # Descargar desde URL
    print("   📥 Descargando desde WFS...")
    try:
        response = requests.get(url, timeout=timeout, verify=verify_ssl)
        response.raise_for_status()

        content = cast(str, response.text)
        print(f"   ✅ Descargado {len(content):,} bytes")

        # Guardar en caché
        save_to_cache(cache_key, content)

        return content

    except requests.RequestException as e:
        print(f"   ❌ Error descargando: {e}")
        # Intentar usar caché viejo si existe
        cache_file = CACHE_DIR / f"{cache_key}.cache"
        if cache_file.exists():
            print("   ⚠️  Usando caché VIEJO como fallback")
            return cache_file.read_text(encoding="utf-8")
        raise

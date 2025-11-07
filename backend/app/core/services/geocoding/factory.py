"""
Factory para crear adapters de geocodificación.

Permite cambiar de proveedor via configuración.
"""

import logging
from typing import Optional

from .base import GeocodingAdapter
from .mapbox_adapter import MapboxAdapter
from .google_maps_adapter import GoogleMapsAdapter

logger = logging.getLogger(__name__)


class GeocodingFactory:
    """Factory para crear adapters de geocodificación."""

    PROVIDERS = {
        "mapbox": MapboxAdapter,
        "google": GoogleMapsAdapter,
        # Fácil agregar más en el futuro:
        # "nominatim": NominatimAdapter,
    }

    @classmethod
    def create_adapter(
        cls,
        provider: str = "mapbox",
        api_key: Optional[str] = None,
        **kwargs,
    ) -> GeocodingAdapter:
        """
        Crea un adapter de geocodificación.

        Args:
            provider: Nombre del proveedor ('mapbox', 'google', 'nominatim', etc.)
            api_key: API key del proveedor (si es necesario)
            **kwargs: Argumentos adicionales para el adapter

        Returns:
            Instancia del adapter configurado

        Raises:
            ValueError: Si el proveedor no es válido o falta configuración
        """
        provider_lower = provider.lower()

        if provider_lower not in cls.PROVIDERS:
            raise ValueError(
                f"Proveedor '{provider}' no soportado. "
                f"Opciones: {', '.join(cls.PROVIDERS.keys())}"
            )

        adapter_class = cls.PROVIDERS[provider_lower]

        # Validar API key para proveedores que lo requieren
        if provider_lower in ["mapbox", "google"] and not api_key:
            raise ValueError(f"API key requerida para proveedor '{provider}'")

        # Crear adapter con configuración
        if provider_lower == "mapbox":
            return adapter_class(access_token=api_key, **kwargs)
        elif provider_lower == "google":
            return adapter_class(api_key=api_key, **kwargs)

        raise ValueError(f"Configuración no implementada para '{provider}'")

    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Retorna lista de proveedores disponibles."""
        return list(cls.PROVIDERS.keys())

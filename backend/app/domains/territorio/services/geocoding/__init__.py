"""
Geocoding services - Adapter pattern para diferentes proveedores.

Permite cambiar entre Mapbox, Google Maps, Nominatim, etc.
"""

from .base import GeocodingAdapter, GeocodingResult
from .factory import GeocodingFactory
from .mapbox_adapter import MapboxAdapter
from .sync_geocoding_service import SyncGeocodingService

__all__ = [
    "GeocodingAdapter",
    "GeocodingResult",
    "GeocodingFactory",
    "MapboxAdapter",
    "SyncGeocodingService",
]

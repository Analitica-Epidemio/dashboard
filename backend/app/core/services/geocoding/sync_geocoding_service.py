"""
Synchronous geocoding service for bulk processors.

Este servicio permite geocodificar direcciones durante el procesamiento de eventos.
Usa asyncio.run() para poder llamar al adapter async desde código sync.
"""

import asyncio
import logging
from decimal import Decimal
from typing import Optional, Tuple

from sqlalchemy import select
from sqlmodel import Session

from app.core.config import settings
from app.domains.territorio.geografia_models import Departamento, Localidad, Provincia

from .base import GeocodingResult
from .factory import GeocodingFactory

logger = logging.getLogger(__name__)


class SyncGeocodingService:
    """Servicio de geocodificación síncrono para bulk processors."""

    def __init__(
        self, session: Session, provider: Optional[str] = None, api_key: Optional[str] = None
    ):
        """
        Inicializa el servicio de geocodificación.

        Args:
            session: Sesión de base de datos
            provider: Proveedor de geocodificación ('mapbox', 'google', etc.)
                     Si no se provee, usa settings.GEOCODING_PROVIDER
            api_key: API key del proveedor (si no se provee, se obtiene de settings)
        """
        self.session = session
        self.provider = provider or settings.GEOCODING_PROVIDER

        # Obtener API key desde settings si no se provee
        if not api_key:
            if self.provider == "mapbox":
                api_key = settings.MAPBOX_ACCESS_TOKEN
            elif self.provider == "google":
                api_key = getattr(settings, "GOOGLE_MAPS_API_KEY", None)

        if not api_key:
            logger.warning(
                f"No API key configurada para {self.provider}. "
                "Geocodificación deshabilitada."
            )
            self.adapter = None
        else:
            try:
                self.adapter = GeocodingFactory.create_adapter(
                    provider=self.provider, api_key=api_key
                )
            except Exception as e:
                logger.error(f"Error creando adapter de geocodificación: {e}")
                self.adapter = None

    def geocode_address(
        self,
        calle: Optional[str] = None,
        numero: Optional[str] = None,
        localidad: Optional[str] = None,
        provincia: Optional[str] = None,
        id_localidad_indec: Optional[int] = None,
    ) -> Optional[GeocodingResult]:
        """
        Geocodifica una dirección.

        Args:
            calle: Calle del domicilio
            numero: Número del domicilio
            localidad: Localidad/ciudad
            provincia: Provincia
            id_localidad_indec: ID INDEC de la localidad (para resolver nombres desde BD)

        Returns:
            GeocodingResult con coordenadas y datos normalizados, o None si falla
        """
        if not self.adapter:
            logger.debug("Geocodificación deshabilitada (no hay adapter)")
            return None

        # Si no se proveen nombres de localidad/provincia, intentar obtenerlos de BD
        if id_localidad_indec and not (localidad or provincia):
            localidad, provincia = self._resolve_geographic_names(id_localidad_indec)

        # Validar que tengamos suficiente información
        if not (calle or localidad):
            logger.debug("No hay suficiente información para geocodificar")
            return None

        try:
            # Llamar al adapter async usando asyncio.run()
            result = asyncio.run(
                self.adapter.geocode(
                    calle=calle,
                    numero=numero,
                    localidad=localidad,
                    provincia=provincia,
                    pais="Argentina",
                )
            )

            if result:
                logger.debug(
                    f"Geocodificado: {calle} {numero}, {localidad} "
                    f"-> ({result.latitud}, {result.longitud})"
                )

            return result

        except Exception as e:
            logger.warning(f"Error en geocodificación: {e}")
            return None

    def resolve_geographic_ids(
        self, latitud: Decimal, longitud: Decimal
    ) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """
        Resuelve IDs de localidad, departamento y provincia desde coordenadas.

        TODO: Implementar búsqueda geográfica usando PostGIS.
        Por ahora retorna None, None, None.

        Args:
            latitud: Latitud
            longitud: Longitud

        Returns:
            Tupla (id_localidad, id_departamento, id_provincia)
        """
        # TODO: Usar PostGIS para buscar la geometría más cercana
        # SELECT id FROM localidad
        # WHERE ST_Contains(geometria, ST_SetSRID(ST_MakePoint(lon, lat), 4326))
        # LIMIT 1

        logger.debug(
            "resolve_geographic_ids no implementado aún - se requiere PostGIS"
        )
        return None, None, None

    def _resolve_geographic_names(
        self, id_localidad_indec: int
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Resuelve nombres de localidad y provincia desde ID INDEC.

        Args:
            id_localidad_indec: ID INDEC de la localidad

        Returns:
            Tupla (nombre_localidad, nombre_provincia)
        """
        try:
            # Buscar localidad con join a departamento y provincia
            stmt = (
                select(Localidad, Departamento, Provincia)
                .join(Departamento, Localidad.id_departamento_indec == Departamento.id_departamento_indec)
                .join(Provincia, Departamento.id_provincia == Provincia.id)
                .where(Localidad.id_localidad_indec == id_localidad_indec)
            )

            result = self.session.execute(stmt).first()

            if result:
                localidad, departamento, provincia = result
                return localidad.nombre, provincia.nombre

        except Exception as e:
            logger.warning(f"Error resolviendo nombres geográficos: {e}")

        return None, None

    def close(self):
        """Cierra el adapter si es necesario."""
        if self.adapter and hasattr(self.adapter, "close"):
            try:
                asyncio.run(self.adapter.close())
            except Exception as e:
                logger.warning(f"Error cerrando adapter: {e}")

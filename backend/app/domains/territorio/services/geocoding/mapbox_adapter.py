"""
Adapter para Mapbox Geocoding API.

Docs: https://docs.mapbox.com/api/search/geocoding/
"""

import logging
from decimal import Decimal
from typing import Optional
from urllib.parse import quote

import httpx

from .base import GeocodingAdapter, GeocodingResult

logger = logging.getLogger(__name__)


class MapboxAdapter(GeocodingAdapter):
    """Adapter para Mapbox Geocoding API."""

    BASE_URL = "https://api.mapbox.com/geocoding/v5/mapbox.places"

    def __init__(self, access_token: str, timeout: int = 10):
        """
        Inicializa el adapter de Mapbox.

        Args:
            access_token: Token de acceso de Mapbox
            timeout: Timeout en segundos para requests HTTP
        """
        self.access_token = access_token
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def geocode(
        self,
        calle: Optional[str] = None,
        numero: Optional[str] = None,
        barrio: Optional[str] = None,
        localidad: Optional[str] = None,
        provincia: Optional[str] = None,
        pais: str = "Argentina",
    ) -> Optional[GeocodingResult]:
        """Geocodifica una dirección usando Mapbox."""
        # Construir query de búsqueda
        address_parts = []

        if calle:
            if numero:
                address_parts.append(f"{calle} {numero}")
            else:
                address_parts.append(calle)

        if barrio:
            address_parts.append(barrio)

        if localidad:
            address_parts.append(localidad)

        if provincia:
            address_parts.append(provincia)

        address_parts.append(pais)

        query = ", ".join(filter(None, address_parts))

        if not query or query == pais:
            logger.warning("No hay suficiente información para geocodificar")
            return None

        try:
            # URL encode query
            encoded_query = quote(query)

            # Construir URL con filtros para Argentina
            url = (
                f"{self.BASE_URL}/{encoded_query}.json"
                f"?access_token={self.access_token}"
                f"&country=AR"  # Filtrar solo Argentina
                f"&language=es"  # Resultados en español
                f"&limit=1"  # Solo el mejor resultado
                f"&types=address"  # Solo direcciones, no lugares/POI/regiones
            )

            logger.debug(f"Geocoding query: {query}")

            response = await self.client.get(url)
            response.raise_for_status()

            data = response.json()

            if not data.get("features"):
                logger.warning(f"No se encontraron resultados para: {query}")
                return None

            feature = data["features"][0]

            # VALIDACIÓN ESTRICTA: Verificar relevance score
            relevance = feature.get("relevance", 0.0)
            if relevance < 0.8:
                logger.warning(
                    f"Resultado con baja relevancia ({relevance:.2f}) para: {query}. "
                    f"Rechazando para evitar geocodificaciones imprecisas."
                )
                return None

            # VALIDACIÓN ESTRICTA: Verificar que sea tipo 'address'
            place_type = feature.get("place_type", [])
            if "address" not in place_type:
                logger.warning(
                    f"Resultado no es tipo 'address' (es {place_type}) para: {query}. "
                    f"Rechazando para evitar matches genéricos (ej: centros de ciudad)."
                )
                return None

            # Extraer coordenadas
            coordinates = feature.get("geometry", {}).get("coordinates", [])
            if len(coordinates) != 2:
                logger.error("Coordenadas inválidas en respuesta de Mapbox")
                return None

            longitude, latitude = coordinates

            # Extraer componentes de la dirección
            context = feature.get("context", [])

            # Parsear context para obtener componentes
            resultado_provincia = None
            resultado_localidad = None
            resultado_barrio = None
            resultado_codigo_postal = None

            for ctx in context:
                ctx_id = ctx.get("id", "")
                ctx_text = ctx.get("text", "")

                if ctx_id.startswith("region."):
                    resultado_provincia = ctx_text
                elif ctx_id.startswith("place."):
                    resultado_localidad = ctx_text
                elif ctx_id.startswith("neighborhood."):
                    resultado_barrio = ctx_text
                elif ctx_id.startswith("postcode."):
                    resultado_codigo_postal = ctx_text

            # Calcular confidence score basado en relevance de Mapbox
            confidence = relevance

            return GeocodingResult(
                latitud=Decimal(str(latitude)),
                longitud=Decimal(str(longitude)),
                calle=calle,  # Mapbox no siempre retorna calle exacta
                numero=numero,
                barrio=resultado_barrio or barrio,
                localidad=resultado_localidad or localidad,
                provincia=resultado_provincia or provincia,
                codigo_postal=resultado_codigo_postal,
                confidence=confidence,
                raw_response=feature,
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"Error HTTP en Mapbox API: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Error de conexión con Mapbox: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado en geocodificación: {e}")
            return None

    async def reverse_geocode(
        self, latitud: Decimal, longitud: Decimal
    ) -> Optional[GeocodingResult]:
        """Geocodificación reversa usando Mapbox."""
        try:
            # Construir URL para reverse geocoding
            url = (
                f"{self.BASE_URL}/{longitud},{latitud}.json"
                f"?access_token={self.access_token}"
                f"&language=es"
                f"&limit=1"
            )

            response = await self.client.get(url)
            response.raise_for_status()

            data = response.json()

            if not data.get("features"):
                logger.warning(
                    f"No se encontraron resultados para: {latitud}, {longitud}"
                )
                return None

            feature = data["features"][0]

            # Extraer componentes
            context = feature.get("context", [])

            resultado_calle = None
            resultado_numero = None
            resultado_provincia = None
            resultado_localidad = None
            resultado_barrio = None
            resultado_codigo_postal = None

            for ctx in context:
                ctx_id = ctx.get("id", "")
                ctx_text = ctx.get("text", "")

                if ctx_id.startswith("region."):
                    resultado_provincia = ctx_text
                elif ctx_id.startswith("place."):
                    resultado_localidad = ctx_text
                elif ctx_id.startswith("neighborhood."):
                    resultado_barrio = ctx_text
                elif ctx_id.startswith("postcode."):
                    resultado_codigo_postal = ctx_text
                elif ctx_id.startswith("address."):
                    resultado_calle = ctx_text

            return GeocodingResult(
                latitud=latitud,
                longitud=longitud,
                calle=resultado_calle,
                numero=resultado_numero,
                barrio=resultado_barrio,
                localidad=resultado_localidad,
                provincia=resultado_provincia,
                codigo_postal=resultado_codigo_postal,
                confidence=feature.get("relevance", 0.0),
                raw_response=feature,
            )

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Error HTTP en Mapbox reverse geocoding: {e.response.status_code}"
            )
            return None
        except httpx.RequestError as e:
            logger.error(f"Error de conexión con Mapbox: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado en reverse geocoding: {e}")
            return None

    def get_provider_name(self) -> str:
        """Retorna el nombre del proveedor."""
        return "Mapbox"

    async def close(self) -> None:
        """Cierra el cliente HTTP."""
        await self.client.aclose()

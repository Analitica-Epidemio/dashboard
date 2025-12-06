"""
Adapter para Google Maps Geocoding API.

Docs: https://developers.google.com/maps/documentation/geocoding/overview
"""

import logging
from decimal import Decimal
from typing import Optional
from urllib.parse import quote

import httpx

from .base import GeocodingAdapter, GeocodingResult

logger = logging.getLogger(__name__)


class GoogleMapsAdapter(GeocodingAdapter):
    """Adapter para Google Maps Geocoding API."""

    BASE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

    def __init__(self, api_key: str, timeout: int = 10):
        """
        Inicializa el adapter de Google Maps.

        Args:
            api_key: API Key de Google Cloud
            timeout: Timeout en segundos para requests HTTP
        """
        self.api_key = api_key
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
        """Geocodifica una dirección usando Google Maps."""
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
            # Construir URL con filtros
            url = (
                f"{self.BASE_URL}"
                f"?address={quote(query)}"
                f"&key={self.api_key}"
                f"&region=ar"  # Bias hacia Argentina
                f"&language=es"  # Resultados en español
                f"&components=country:AR"  # Filtrar solo Argentina (estricto)
            )

            logger.debug(f"Geocoding query: {query}")

            response = await self.client.get(url)
            response.raise_for_status()

            data = response.json()

            # Verificar status de Google
            if data.get("status") != "OK":
                logger.warning(
                    f"Google Maps no encontró resultados para: {query} (status: {data.get('status')})"
                )
                return None

            if not data.get("results"):
                logger.warning(f"No se encontraron resultados para: {query}")
                return None

            result = data["results"][0]

            # VALIDACIÓN ESTRICTA 1: Verificar location_type
            geometry = result.get("geometry", {})
            location_type = geometry.get("location_type", "")

            # ROOFTOP = dirección exacta
            # RANGE_INTERPOLATED = interpolado entre números
            # GEOMETRIC_CENTER = centro geométrico (menos preciso)
            # APPROXIMATE = muy impreciso (rechazar)
            if location_type == "APPROXIMATE":
                logger.warning(
                    f"Resultado muy impreciso (APPROXIMATE) para: {query}. "
                    f"Rechazando para evitar geocodificaciones genéricas."
                )
                return None

            # VALIDACIÓN ESTRICTA 2: Verificar tipos de resultado
            result_types = result.get("types", [])

            # Aceptar solo resultados de tipo dirección
            # Rechazar: locality, administrative_area, etc (muy genéricos)
            valid_types = {
                "street_address",       # Dirección completa con número
                "premise",              # Edificio/propiedad específica
                "subpremise",          # Unidad dentro de edificio
                "route",               # Calle (sin número pero válida)
            }

            if not any(t in valid_types for t in result_types):
                logger.warning(
                    f"Resultado no es tipo dirección (tipos: {result_types}) para: {query}. "
                    f"Rechazando para evitar matches genéricos."
                )
                return None

            # Extraer coordenadas
            location = geometry.get("location", {})
            latitude = location.get("lat")
            longitude = location.get("lng")

            if latitude is None or longitude is None:
                logger.error("Coordenadas inválidas en respuesta de Google Maps")
                return None

            # Extraer componentes de la dirección
            address_components = result.get("address_components", [])

            resultado_calle = None
            resultado_numero = None
            resultado_barrio = None
            resultado_localidad = None
            resultado_departamento = None
            resultado_provincia = None
            resultado_codigo_postal = None

            for component in address_components:
                types = component.get("types", [])
                long_name = component.get("long_name", "")

                if "street_number" in types:
                    resultado_numero = long_name
                elif "route" in types:
                    resultado_calle = long_name
                elif "sublocality" in types or "neighborhood" in types:
                    resultado_barrio = long_name
                elif "locality" in types:
                    resultado_localidad = long_name
                elif "administrative_area_level_2" in types:
                    resultado_departamento = long_name
                elif "administrative_area_level_1" in types:
                    resultado_provincia = long_name
                elif "postal_code" in types:
                    resultado_codigo_postal = long_name

            # Calcular confidence score basado en location_type
            confidence_map = {
                "ROOFTOP": 1.0,              # Dirección exacta
                "RANGE_INTERPOLATED": 0.9,   # Interpolado
                "GEOMETRIC_CENTER": 0.75,    # Centro geométrico
                "APPROXIMATE": 0.5,          # Aproximado (ya rechazamos antes)
            }
            confidence = confidence_map.get(location_type, 0.8)

            return GeocodingResult(
                latitud=Decimal(str(latitude)),
                longitud=Decimal(str(longitude)),
                calle=resultado_calle or calle,
                numero=resultado_numero or numero,
                barrio=resultado_barrio or barrio,
                localidad=resultado_localidad or localidad,
                departamento=resultado_departamento,
                provincia=resultado_provincia or provincia,
                codigo_postal=resultado_codigo_postal,
                confidence=confidence,
                raw_response=result,
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"Error HTTP en Google Maps API: {e.response.status_code}")
            if e.response.status_code == 403:
                logger.error("API Key inválida o sin permisos para Geocoding API")
            return None
        except httpx.RequestError as e:
            logger.error(f"Error de conexión con Google Maps: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado en geocodificación: {e}")
            return None

    async def reverse_geocode(
        self, latitud: Decimal, longitud: Decimal
    ) -> Optional[GeocodingResult]:
        """Geocodificación reversa usando Google Maps."""
        try:
            # Construir URL para reverse geocoding
            url = (
                f"{self.BASE_URL}"
                f"?latlng={latitud},{longitud}"
                f"&key={self.api_key}"
                f"&language=es"
                f"&result_type=street_address"  # Solo direcciones
            )

            response = await self.client.get(url)
            response.raise_for_status()

            data = response.json()

            if data.get("status") != "OK":
                logger.warning(
                    f"Google Maps reverse geocoding falló para: {latitud}, {longitud} (status: {data.get('status')})"
                )
                return None

            if not data.get("results"):
                logger.warning(
                    f"No se encontraron resultados para: {latitud}, {longitud}"
                )
                return None

            result = data["results"][0]

            # Extraer componentes
            address_components = result.get("address_components", [])

            resultado_calle = None
            resultado_numero = None
            resultado_barrio = None
            resultado_localidad = None
            resultado_departamento = None
            resultado_provincia = None
            resultado_codigo_postal = None

            for component in address_components:
                types = component.get("types", [])
                long_name = component.get("long_name", "")

                if "street_number" in types:
                    resultado_numero = long_name
                elif "route" in types:
                    resultado_calle = long_name
                elif "sublocality" in types or "neighborhood" in types:
                    resultado_barrio = long_name
                elif "locality" in types:
                    resultado_localidad = long_name
                elif "administrative_area_level_2" in types:
                    resultado_departamento = long_name
                elif "administrative_area_level_1" in types:
                    resultado_provincia = long_name
                elif "postal_code" in types:
                    resultado_codigo_postal = long_name

            # Confidence basado en location_type
            geometry = result.get("geometry", {})
            location_type = geometry.get("location_type", "")
            confidence_map = {
                "ROOFTOP": 1.0,
                "RANGE_INTERPOLATED": 0.9,
                "GEOMETRIC_CENTER": 0.75,
                "APPROXIMATE": 0.5,
            }
            confidence = confidence_map.get(location_type, 0.8)

            return GeocodingResult(
                latitud=latitud,
                longitud=longitud,
                calle=resultado_calle,
                numero=resultado_numero,
                barrio=resultado_barrio,
                localidad=resultado_localidad,
                departamento=resultado_departamento,
                provincia=resultado_provincia,
                codigo_postal=resultado_codigo_postal,
                confidence=confidence,
                raw_response=result,
            )

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Error HTTP en Google Maps reverse geocoding: {e.response.status_code}"
            )
            return None
        except httpx.RequestError as e:
            logger.error(f"Error de conexión con Google Maps: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado en reverse geocoding: {e}")
            return None

    def get_provider_name(self) -> str:
        """Retorna el nombre del proveedor."""
        return "Google Maps"

    async def close(self):
        """Cierra el cliente HTTP."""
        await self.client.aclose()

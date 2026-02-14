"""
Base adapter interface para servicios de geocodificación.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class GeocodingResult:
    """Resultado de geocodificación normalizado."""

    latitud: Decimal | None
    longitud: Decimal | None
    calle: str | None = None
    numero: str | None = None
    barrio: str | None = None
    localidad: str | None = None
    departamento: str | None = None
    provincia: str | None = None
    codigo_postal: str | None = None
    confidence: float = 0.0
    raw_response: dict | None = None


class GeocodingAdapter(ABC):
    """Interface base para adapters de geocodificación."""

    @abstractmethod
    async def geocode(
        self,
        calle: str | None = None,
        numero: str | None = None,
        barrio: str | None = None,
        localidad: str | None = None,
        provincia: str | None = None,
        pais: str = "Argentina",
    ) -> GeocodingResult | None:
        """
        Geocodifica una dirección.

        Args:
            calle: Nombre de la calle
            numero: Número de calle
            barrio: Barrio
            localidad: Localidad/ciudad
            provincia: Provincia
            pais: País (default: Argentina)

        Returns:
            GeocodingResult con coordenadas y datos normalizados, o None si falla
        """

    @abstractmethod
    async def reverse_geocode(
        self, latitud: Decimal, longitud: Decimal
    ) -> GeocodingResult | None:
        """
        Geocodificación reversa: de coordenadas a dirección.

        Args:
            latitud: Latitud
            longitud: Longitud

        Returns:
            GeocodingResult con dirección normalizada, o None si falla
        """

    @abstractmethod
    def get_provider_name(self) -> str:
        """Retorna el nombre del proveedor."""

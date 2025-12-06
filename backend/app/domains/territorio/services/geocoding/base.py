"""
Base adapter interface para servicios de geocodificación.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class GeocodingResult:
    """Resultado de geocodificación normalizado."""

    latitud: Optional[Decimal]
    longitud: Optional[Decimal]
    calle: Optional[str] = None
    numero: Optional[str] = None
    barrio: Optional[str] = None
    localidad: Optional[str] = None
    departamento: Optional[str] = None
    provincia: Optional[str] = None
    codigo_postal: Optional[str] = None
    confidence: float = 0.0
    raw_response: Optional[dict] = None


class GeocodingAdapter(ABC):
    """Interface base para adapters de geocodificación."""

    @abstractmethod
    async def geocode(
        self,
        calle: Optional[str] = None,
        numero: Optional[str] = None,
        barrio: Optional[str] = None,
        localidad: Optional[str] = None,
        provincia: Optional[str] = None,
        pais: str = "Argentina",
    ) -> Optional[GeocodingResult]:
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
        pass

    @abstractmethod
    async def reverse_geocode(
        self, latitud: Decimal, longitud: Decimal
    ) -> Optional[GeocodingResult]:
        """
        Geocodificación reversa: de coordenadas a dirección.

        Args:
            latitud: Latitud
            longitud: Longitud

        Returns:
            GeocodingResult con dirección normalizada, o None si falla
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Retorna el nombre del proveedor."""
        pass

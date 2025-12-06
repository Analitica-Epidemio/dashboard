"""
TopoJSON optimization utilities for efficient geospatial data serving.
Provides quantization, compression, and lazy loading capabilities.
"""

import gzip
import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class TopoJSONOptimizer:
    """Handles TopoJSON optimization and compression"""

    def __init__(self, topojson_dir: str):
        self.topojson_dir = Path(topojson_dir)
        self._cache: Dict[str, bytes] = {}

    def _quantize_geometry(
        self, coords: Any, decimals: int = 4
    ) -> Any:
        """
        Quantize coordinate precision to reduce JSON size.

        Uses rounding to specified decimal places (default 4 decimals).
        This reduces file size when JSON is minified while maintaining visual accuracy.
        For Argentina maps, 4 decimals = ~11 meter precision, sufficient for epidemiological data.
        """
        if not isinstance(coords, (list, tuple)):
            return coords

        if len(coords) == 0:
            return coords

        # Check if this is a coordinate pair
        if isinstance(coords[0], (int, float)):
            # Round to specified decimal places
            multiplier = 10 ** decimals
            return [round(c * multiplier) / multiplier for c in coords]

        # Recursively process nested arrays
        return [self._quantize_geometry(c, decimals) for c in coords]

    def _quantize_topojson(self, data: Dict[str, Any], decimals: int = 4) -> Dict[str, Any]:
        """Quantize all coordinates in TopoJSON to reduce JSON size"""
        result = data.copy()

        # Quantize arcs (the main geometry store in TopoJSON)
        if "arcs" in result:
            result["arcs"] = [
                self._quantize_geometry(arc, decimals) for arc in result["arcs"]
            ]

        return result

    def _compress_gzip(self, data: bytes, level: int = 9) -> bytes:
        """Compress data using gzip with maximum compression"""
        return gzip.compress(data, compresslevel=level)

    def load_topojson(
        self,
        filename: str,
        compress: bool = True,
        quantize: bool = True,
        quantize_decimals: int = 4,
    ) -> tuple[bytes, str]:
        """
        Load and optimize TopoJSON file.

        Args:
            filename: Name of the TopoJSON file (e.g., "departamentos-argentina.topojson")
            compress: Whether to apply gzip compression
            quantize: Whether to quantize coordinates
            quantize_decimals: Decimal places for coordinate rounding (4 = ~11m accuracy)

        Returns:
            Tuple of (compressed_bytes, content_type)
        """
        # Check cache first
        cache_key = f"{filename}:compress={compress}:quantize={quantize}:{quantize_decimals}"
        if cache_key in self._cache:
            logger.debug(f"Cache hit for {cache_key}")
            return self._cache[cache_key], "application/json"

        file_path = self.topojson_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"TopoJSON file not found: {filename}")

        # Load JSON
        with open(file_path, "r") as f:
            data = json.load(f)

        # Apply quantization if enabled
        if quantize:
            logger.debug(f"Quantizing {filename} to {quantize_decimals} decimals")
            data = self._quantize_topojson(data, quantize_decimals)

        # Convert to JSON bytes with minification
        json_bytes = json.dumps(data, separators=(",", ":")).encode("utf-8")

        # Apply compression if enabled
        if compress:
            logger.debug(f"Compressing {filename}")
            json_bytes = self._compress_gzip(json_bytes)
            content_type = "application/json+gzip"
        else:
            content_type = "application/json"

        # Cache the result
        self._cache[cache_key] = json_bytes
        logger.debug(
            f"Cached {filename}: {len(json_bytes)} bytes "
            f"(compress={compress}, quantize={quantize})"
        )

        return json_bytes, content_type

    def get_available_files(self) -> list[str]:
        """Get list of available TopoJSON files"""
        if not self.topojson_dir.exists():
            return []
        return [f.name for f in self.topojson_dir.glob("*.topojson")]

    def get_file_info(self, filename: str) -> Dict[str, Any]:
        """Get information about a TopoJSON file"""
        file_path = self.topojson_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"TopoJSON file not found: {filename}")

        # Get original size
        original_size = file_path.stat().st_size

        # Load and check structure
        with open(file_path, "r") as f:
            data = json.load(f)

        objects = list(data.get("objects", {}).keys())
        has_transform = "transform" in data

        return {
            "filename": filename,
            "original_size_bytes": original_size,
            "objects": objects,
            "has_transform": has_transform,
            "arcs_count": len(data.get("arcs", [])) if "arcs" in data else 0,
        }

    def estimate_compression(self, filename: str, decimals: int = 4) -> Dict[str, Any]:
        """Estimate compression ratios for a file"""
        file_path = self.topojson_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"TopoJSON file not found: {filename}")

        with open(file_path, "r") as f:
            data = json.load(f)

        # Original size
        original_json = json.dumps(data, separators=(",", ":")).encode("utf-8")
        original_size = len(original_json)

        # Compressed size
        compressed = gzip.compress(original_json, compresslevel=9)
        compressed_size = len(compressed)

        # Quantized size
        quantized = self._quantize_topojson(data, decimals)
        quantized_json = json.dumps(quantized, separators=(",", ":")).encode("utf-8")
        quantized_size = len(quantized_json)

        # Quantized + compressed
        quantized_compressed = gzip.compress(quantized_json, compresslevel=9)
        quantized_compressed_size = len(quantized_compressed)

        return {
            "filename": filename,
            "original_size": original_size,
            "compressed_size": compressed_size,
            "compression_ratio": f"{(1 - compressed_size / original_size) * 100:.1f}%",
            "quantized_size": quantized_size,
            "quantized_ratio": f"{(1 - quantized_size / original_size) * 100:.1f}%",
            "quantized_compressed_size": quantized_compressed_size,
            "quantized_compressed_ratio": f"{(1 - quantized_compressed_size / original_size) * 100:.1f}%",
        }

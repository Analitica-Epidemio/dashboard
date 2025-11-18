"""
Helpers para renderizar el HTML de boletines reemplazando nodos dinámicos de charts.
Convierte los placeholders TipTap (divs con data-type="dynamic-chart") a imágenes
renderizadas server-side usando ChartSpecGenerator + ChartRenderer.
"""

from __future__ import annotations

import base64
import html
import logging
import re
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.chart_spec import ChartFilters
from app.services.chart_renderer import chart_renderer
from app.services.chart_spec_generator import ChartSpecGenerator

logger = logging.getLogger(__name__)


class BulletinHTMLRenderer:
    """Procesa contenido HTML de boletines y reemplaza charts dinámicos por imágenes."""

    _CHART_DIV_PATTERN = re.compile(
        r"<div(?P<attrs>[^>]*data-type=['\"]dynamic-chart['\"][^>]*)>(?P<inner>.*?)</div>",
        re.IGNORECASE | re.DOTALL,
    )
    _ATTR_PATTERN = re.compile(r"([a-zA-Z0-9_-]+)\s*=\s*['\"](.*?)['\"]", re.DOTALL)

    def __init__(self, db: AsyncSession):
        self.db = db
        self.generator = ChartSpecGenerator(db)

    async def render_html_with_charts(self, html_content: str) -> str:
        """Reemplaza nodos dinámicos por imágenes en base64 listas para incrustar."""
        if not html_content:
            return html_content

        rendered_parts: List[str] = []
        last_idx = 0

        for match in self._CHART_DIV_PATTERN.finditer(html_content):
            start, end = match.span()
            rendered_parts.append(html_content[last_idx:start])
            attrs_raw = match.group("attrs") or ""
            replacement = await self._render_chart_block(attrs_raw)
            rendered_parts.append(replacement)
            last_idx = end

        rendered_parts.append(html_content[last_idx:])
        return "".join(rendered_parts)

    async def _render_chart_block(self, attrs_raw: str) -> str:
        attrs = self._parse_attributes(attrs_raw)

        chart_code = self._extract_attr(attrs, "chartcode")
        if not chart_code:
            return self._error_block("Gráfico sin código especificado.")

        evento_ids = self._parse_ids(self._extract_attr(attrs, "eventoids"))
        if not evento_ids:
            return self._error_block(f"No hay eventos configurados para '{chart_code}'.")

        grupo_ids = self._parse_ids(self._extract_attr(attrs, "grupoids"))
        fecha_desde = self._extract_attr(attrs, "fechadesde")
        fecha_hasta = self._extract_attr(attrs, "fechahasta")
        title = self._extract_attr(attrs, "title")

        filters = ChartFilters(
            grupo_eno_ids=grupo_ids,
            tipo_eno_ids=evento_ids,
            fecha_desde=fecha_desde or None,
            fecha_hasta=fecha_hasta or None,
        )

        try:
            spec = await self.generator.generate_spec(
                chart_code=chart_code,
                filters=filters,
                config={"height": 420},
            )
            img_bytes = chart_renderer.render_to_bytes(spec, dpi=220)

            b64_img = base64.b64encode(img_bytes).decode("utf-8")
            alt_text = html.escape(title or spec.title or chart_code)

            title_html = ""
            if title:
                title_html = (
                    f'<h4 style="margin: 0 0 0.5rem; color: #1e3a8a; font-size: 1rem;">'
                    f"{html.escape(title)}</h4>"
                )

            return (
                '<div class="chart-block" style="margin: 1.5rem 0; text-align: center;">'
                f"{title_html}"
                f'<img src="data:image/png;base64,{b64_img}" '
                f'style="max-width: 100%; height: auto; border: 1px solid #e5e7eb; '
                f'border-radius: 0.5rem; padding: 0.5rem;" alt="{alt_text}"/>'
                '<p style="font-size: 0.75rem; color: #6b7280; margin-top: 0.35rem;">'
                "Generado automáticamente con datos del Sistema de Vigilancia Epidemiológica"
                "</p>"
                "</div>"
            )
        except Exception as exc:
            logger.exception("Error renderizando chart %s: %s", chart_code, exc)
            return self._error_block(f"No se pudo renderizar el gráfico '{chart_code}'.")

    def _parse_attributes(self, attrs_raw: str) -> Dict[str, str]:
        attrs: Dict[str, str] = {}
        for key, value in self._ATTR_PATTERN.findall(attrs_raw):
            normalized_key = self._normalize_attr_name(key)
            attrs[normalized_key] = value.strip()
        return attrs

    def _normalize_attr_name(self, attr_name: str) -> str:
        normalized = attr_name.lower()
        if normalized.startswith("data-"):
            normalized = normalized[5:]
        normalized = normalized.replace("-", "").replace("_", "")
        return normalized

    def _extract_attr(self, attrs: Dict[str, str], key: str) -> Optional[str]:
        normalized_key = self._normalize_attr_name(key)
        return attrs.get(normalized_key)

    def _parse_ids(self, raw_value: Optional[str]) -> Optional[List[int]]:
        if not raw_value:
            return None

        ids: List[int] = []
        for part in re.split(r"[,\s]+", raw_value.strip()):
            if not part:
                continue
            try:
                ids.append(int(part))
            except ValueError:
                logger.debug("ID inválido ignorado en lista de charts: %s", part)
        return ids or None

    def _error_block(self, message: str) -> str:
        return (
            '<div class="chart-error" style="margin: 1rem 0; padding: 1rem; '
            'border: 1px solid #fecaca; background: #fef2f2; color: #b91c1c; border-radius: 0.5rem;">'
            f"{html.escape(message)}"
            "</div>"
        )

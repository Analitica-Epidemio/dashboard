"""
Renderizador HTML para boletines epidemiologicos.

Convierte contenido HTML con placeholders de graficos a HTML con imagenes embebidas,
procesa saltos de pagina, variables y tablas dinamicas.
"""

import base64
import contextlib
import logging
import re
from typing import TYPE_CHECKING, Any, Optional

from app.domains.charts.schemas import CodigoGrafico

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.domains.boletines.models import BoletinInstance

logger = logging.getLogger(__name__)

# Mapeo de slugs de frontend → código canónico de gráfico (CodigoGrafico).
# Incluye slugs genéricos del catálogo de charts y slugs de bloques de boletín
# definidos en secciones_bloques.py.
# IMPORTANTE: Todo slug de chart que use el frontend DEBE estar en este mapa.
CHART_CODE_MAP: dict[str, CodigoGrafico] = {
    # ── Slugs genéricos del catálogo de charts ──
    "curva-epidemiologica": CodigoGrafico.CURVA_EPIDEMIOLOGICA,
    "corredor-endemico": CodigoGrafico.CORREDOR_ENDEMICO,
    "piramide-poblacional": CodigoGrafico.PIRAMIDE_EDAD,
    "mapa-geografico": CodigoGrafico.MAPA_CHUBUT,
    "estacionalidad-mensual": CodigoGrafico.ESTACIONALIDAD,
    "casos-edad": CodigoGrafico.CASOS_EDAD,
    "distribucion-clasificacion": CodigoGrafico.DISTRIBUCION_CLASIFICACION,
    # ── Slugs de bloques de boletín (secciones_bloques.py) ──
    # Sección IRA
    "corredor-eti": CodigoGrafico.CORREDOR_ENDEMICO,
    "corredor-neumonia": CodigoGrafico.CORREDOR_ENDEMICO,
    # Sección Bronquiolitis
    "corredor-bronquiolitis": CodigoGrafico.CORREDOR_ENDEMICO,
    "ira-por-edad": CodigoGrafico.CASOS_EDAD,
    # Sección Virus Respiratorios
    "virus-resp-semana": CodigoGrafico.CURVA_EPIDEMIOLOGICA,
    "virus-resp-edad": CodigoGrafico.CASOS_EDAD,
    # Sección CO
    "casos-co": CodigoGrafico.CURVA_EPIDEMIOLOGICA,
    # Sección Diarreas
    "corredor-diarrea": CodigoGrafico.CORREDOR_ENDEMICO,
    "agentes-diarrea-semana": CodigoGrafico.CURVA_EPIDEMIOLOGICA,
    # Sección SUH
    "suh-serie-historica": CodigoGrafico.CURVA_EPIDEMIOLOGICA,
    # ── Slugs de eventos nominales (curva-{slug-evento}) ──
    "curva-vih-expuesto-perinatal": CodigoGrafico.CURVA_EPIDEMIOLOGICA,
    "curva-araneismo-envenenamiento-por-loxosceles": CodigoGrafico.CURVA_EPIDEMIOLOGICA,
    "curva-araneismo-envenenamiento-por-latrodectus": CodigoGrafico.CURVA_EPIDEMIOLOGICA,
    "curva-estudio-de-sars-cov-2-en-situaciones-especiales": CodigoGrafico.CURVA_EPIDEMIOLOGICA,
}

# Regex patterns for custom elements
_RE_DYNAMIC_CHART = re.compile(
    r'<div\b[^>]*\bdata-type="dynamic-chart"[^>]*>.*?</div>',
    re.DOTALL | re.IGNORECASE,
)
_RE_PAGE_BREAK = re.compile(
    r'<div\b[^>]*\bdata-type="page-break"[^>]*>.*?</div>',
    re.DOTALL | re.IGNORECASE,
)
_RE_VARIABLE = re.compile(
    r'<span\b[^>]*\bdata-type="variable"[^>]*>.*?</span>',
    re.DOTALL | re.IGNORECASE,
)
_RE_DYNAMIC_TABLE = re.compile(
    r'<div\b[^>]*\bdata-type="dynamic-table"[^>]*>.*?</div>',
    re.DOTALL | re.IGNORECASE,
)


def _resolve_chart_code(code: str) -> CodigoGrafico:
    """Resuelve un código de chart al CodigoGrafico canónico del backend.

    Acepta tanto valores canónicos del enum (snake_case) como slugs legacy (kebab-case).

    Raises:
        KeyError: Si el código no es un CodigoGrafico válido ni está en CHART_CODE_MAP.
    """
    # Primero intentar como valor directo del enum
    try:
        return CodigoGrafico(code)
    except ValueError:
        pass
    # Luego buscar en el mapa de slugs legacy
    try:
        return CHART_CODE_MAP[code]
    except KeyError:
        raise KeyError(
            f"Chart code '{code}' no es un CodigoGrafico válido ni está en CHART_CODE_MAP."
        ) from None


def _extract_attr(tag_html: str, attr_name: str) -> str:
    """Extract an attribute value from an HTML tag string."""
    pattern = rf'{attr_name}="([^"]*)"'
    match = re.search(pattern, tag_html, re.IGNORECASE)
    if match:
        return match.group(1)
    pattern = rf"{attr_name}='([^']*)'"
    match = re.search(pattern, tag_html, re.IGNORECASE)
    if match:
        return match.group(1)
    return ""


def _parse_ids(value: str) -> list[int]:
    """Parse comma-separated IDs string to list of integers."""
    if not value:
        return []
    result = []
    for x in value.split(","):
        x = x.strip()
        if x:
            with contextlib.suppress(ValueError):
                result.append(int(x))
    return result


class BulletinHTMLRenderer:
    """
    Renderiza HTML de boletines con graficos convertidos a imagenes.
    """

    def __init__(
        self,
        db: "AsyncSession",
        instance: Optional["BoletinInstance"] = None,
    ):
        """
        Args:
            db: Sesion de base de datos para consultas de graficos.
            instance: Instancia de boletin para sustitucion de variables.
        """
        self.db = db
        self.instance = instance

    async def render_html_with_charts(self, html_content: str) -> str:
        """Alias para renderizar_html_con_graficos."""
        return await self.renderizar_html_con_graficos(html_content)

    async def renderizar_html_con_graficos(self, html_content: str) -> str:
        """
        Renderiza HTML reemplazando:
        - Graficos dinamicos con imagenes base64
        - Saltos de pagina con CSS page-break
        - Variables con sus valores reales
        - Tablas dinamicas con placeholders
        """
        # 1. Process dynamic charts → base64 images
        html_content = await self._process_charts(html_content)

        # 2. Process page breaks → CSS page-break
        html_content = self._process_page_breaks(html_content)

        # 3. Process variables → substitute values
        html_content = self._process_variables(html_content)

        # 4. Process dynamic tables → placeholder
        html_content = self._process_dynamic_tables(html_content)

        return html_content

    async def _process_charts(self, html: str) -> str:
        """Find all dynamic-chart divs and replace with rendered chart images."""
        from app.domains.charts.schemas import FiltrosGrafico
        from app.domains.charts.services.renderer import chart_renderer
        from app.domains.charts.services.spec_generator import ChartSpecGenerator

        matches = list(_RE_DYNAMIC_CHART.finditer(html))
        if not matches:
            return html

        generator = ChartSpecGenerator(self.db)

        # Process in reverse order to preserve string positions
        for match in reversed(matches):
            tag_html = match.group(0)
            chart_code_raw = _extract_attr(tag_html, "chartcode")

            try:
                chart_code = _resolve_chart_code(chart_code_raw)
                title = _extract_attr(tag_html, "title")
                grupo_ids = _parse_ids(_extract_attr(tag_html, "grupoids"))
                evento_ids = _parse_ids(_extract_attr(tag_html, "eventoids"))
                fecha_desde = _extract_attr(tag_html, "fechadesde")
                fecha_hasta = _extract_attr(tag_html, "fechahasta")

                if not chart_code:
                    logger.warning("Chart sin código, saltando")
                    continue

                # Build filters
                filtros = FiltrosGrafico(
                    ids_grupo_eno=grupo_ids if grupo_ids else None,
                    ids_tipo_eno=evento_ids if evento_ids else None,
                    fecha_desde=fecha_desde or None,
                    fecha_hasta=fecha_hasta or None,
                )

                # Generate spec with real data
                spec = await generator.generar_spec(
                    codigo_grafico=chart_code,
                    filtros=filtros,
                    configuracion={"height": 400},
                )

                # Render to PNG at 200 DPI (good balance of quality vs size)
                img_bytes = chart_renderer.renderizar_a_bytes(spec, dpi=200)
                img_b64 = base64.b64encode(img_bytes).decode("utf-8")

                # Build replacement HTML
                parts = []
                if title:
                    parts.append(
                        f'<p style="font-size: 11pt; font-weight: 600; '
                        f'color: #1f2937; margin-bottom: 8px; text-align: center;">'
                        f"{title}</p>"
                    )
                parts.append(
                    f'<img src="data:image/png;base64,{img_b64}" '
                    f'style="max-width: 100%; height: auto; display: block; '
                    f'margin: 0 auto 16px auto;" '
                    f'alt="{title or chart_code}">'
                )
                replacement = "\n".join(parts)

                html = html[: match.start()] + replacement + html[match.end() :]
                logger.info("Chart '%s' renderizado para PDF", chart_code)

            except Exception as e:
                logger.error("Error procesando chart '%s': %s", chart_code_raw, e)
                replacement = (
                    '<div style="border: 1px solid #e5e7eb; padding: 20px; '
                    "text-align: center; color: #6b7280; margin: 16px 0; "
                    'border-radius: 4px;">'
                    f"<p>Error al generar gráfico: {chart_code_raw or 'desconocido'}</p>"
                    "</div>"
                )
                html = html[: match.start()] + replacement + html[match.end() :]

        return html

    def _process_page_breaks(self, html: str) -> str:
        """Convert page-break divs to CSS page-break-before."""
        return _RE_PAGE_BREAK.sub(
            '<div style="page-break-before: always;"></div>',
            html,
        )

    def _process_variables(self, html: str) -> str:
        """Substitute variable placeholders with actual values."""
        if not self.instance:
            return html

        variables = self._build_variable_values()

        def _replace_variable(match: re.Match) -> str:
            tag_html = match.group(0)
            var_key = _extract_attr(tag_html, "data-variable-key")
            if not var_key:
                return tag_html
            value = variables.get(var_key)
            if value is not None:
                return f'<span style="font-weight: 600;">{value}</span>'
            # Keep original text content if no value found
            return tag_html

        return _RE_VARIABLE.sub(_replace_variable, html)

    def _build_variable_values(self) -> dict[str, Any]:
        """Build variable values from instance metadata."""
        if not self.instance:
            return {}

        inst = self.instance
        values: dict[str, Any] = {}

        if inst.anio_epidemiologico:
            values["anio_epidemiologico"] = str(inst.anio_epidemiologico)
        if inst.semana_epidemiologica:
            values["semana_epidemiologica_actual"] = str(inst.semana_epidemiologica)
        if inst.fecha_inicio:
            values["fecha_inicio_semana_epidemiologica"] = inst.fecha_inicio.strftime(
                "%d/%m/%Y"
            )
        if inst.fecha_fin:
            values["fecha_fin_semana_epidemiologica"] = inst.fecha_fin.strftime(
                "%d/%m/%Y"
            )
        if inst.num_semanas:
            values["num_semanas_analizadas"] = str(inst.num_semanas)
            if inst.semana_epidemiologica:
                se_inicio = inst.semana_epidemiologica - inst.num_semanas + 1
                values["semana_epidemiologica_inicio"] = str(max(1, se_inicio))

        # Also pull values from instance.parameters
        params = inst.parameters or {}
        for key, val in params.items():
            if key not in values and val is not None:
                values[key] = str(val)

        return values

    def _process_dynamic_tables(self, html: str) -> str:
        """Process dynamic table placeholders."""
        table_labels = {
            "top_enos": "Eventos más frecuentes",
            "capacidad_hospitalaria": "Capacidad Hospitalaria",
            "casos_suh": "Casos de SUH",
        }

        def _replace_table(match: re.Match) -> str:
            tag_html = match.group(0)
            title = _extract_attr(tag_html, "title")
            query_type = _extract_attr(tag_html, "querytype")
            table_name = table_labels.get(query_type, query_type)

            parts = []
            if title:
                parts.append(
                    f'<p style="font-size: 11pt; font-weight: 600; '
                    f'color: #1f2937; margin-bottom: 8px;">{title}</p>'
                )
            parts.append(
                f'<div style="border: 1px solid #e5e7eb; padding: 16px; '
                f"text-align: center; color: #6b7280; margin: 16px 0; "
                f'border-radius: 4px; background: #f9fafb;">'
                f'<p style="font-size: 10pt;">[Tabla dinámica: {table_name}]</p>'
                f"</div>"
            )
            return "\n".join(parts)

        return _RE_DYNAMIC_TABLE.sub(_replace_table, html)

"""
Server-Side PDF Generator
Genera PDFs 100% server-side con matplotlib + SVG rendering
Sin dependencias del frontend ni navegadores
"""

import asyncio
import io
import logging
import os
from datetime import datetime
from typing import Any

from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.charts.schemas import CodigoGrafico, FiltrosGrafico
from app.domains.charts.services.renderer import chart_renderer
from app.domains.charts.services.spec_generator import ChartSpecGenerator

logger = logging.getLogger(__name__)

# ── Font registration ───────────────────────────────────────────────────────
# En Docker, Geist se instala en /usr/share/fonts/truetype/geist/.
# Fallback a Roboto (fonts-roboto) o Helvetica si no está disponible.

_GEIST_FONT_DIR = "/usr/share/fonts/truetype/geist"
_ROBOTO_FONT_DIR = "/usr/share/fonts/truetype/roboto"

# Variantes que registramos: (archivo, peso CSS, estilo CSS)
_FONT_VARIANTS = [
    ("Regular", "normal", "normal"),
    ("Bold", "bold", "normal"),
    ("SemiBold", "600", "normal"),
    ("Medium", "500", "normal"),
    ("Light", "300", "normal"),
]


def _build_font_face_css() -> tuple[str, str]:
    """
    Genera @font-face CSS para la mejor fuente disponible.
    Prioridad: Geist > Roboto > Helvetica (fallback).
    """
    for family, font_dir in [("Geist", _GEIST_FONT_DIR), ("Roboto", _ROBOTO_FONT_DIR)]:
        if not os.path.isdir(font_dir):
            continue
        faces: list[str] = []
        for variant, weight, style in _FONT_VARIANTS:
            path = os.path.join(font_dir, f"{family}-{variant}.ttf")
            if os.path.isfile(path):
                faces.append(
                    f"@font-face {{\n"
                    f"  font-family: '{family}';\n"
                    f"  src: url('file://{path}');\n"
                    f"  font-weight: {weight};\n"
                    f"  font-style: {style};\n"
                    f"}}"
                )
        if faces:
            logger.info("PDF font: '%s' (%d variantes)", family, len(faces))
            return "\n".join(faces), family

    logger.info("PDF font: sin fuentes custom, usando Helvetica")
    return "", "Helvetica"


# Se calcula una vez al importar el módulo
_FONT_FACE_CSS, _FONT_FAMILY = _build_font_face_css()


class ServerSidePDFGenerator:
    """
    Genera PDFs de reportes epidemiológicos 100% server-side
    Sin necesidad de navegador ni Playwright
    """

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self._base_html_css = _FONT_FACE_CSS + """
        @page {
            size: A4;
            margin: 20mm;
        }
        body {
            font-family: '""" + _FONT_FAMILY + """', 'Helvetica', 'Arial', sans-serif;
            color: #111827;
            line-height: 1.5;
            font-size: 11pt;
        }
        h1 {
            font-size: 22pt;
            font-weight: normal;
            color: #111827;
            margin-bottom: 0.75rem;
            margin-top: 1.5rem;
        }
        h2 {
            font-size: 18pt;
            font-weight: normal;
            color: #111827;
            margin-bottom: 0.5rem;
            margin-top: 1.25rem;
        }
        h3 {
            font-size: 15pt;
            font-weight: normal;
            color: #111827;
            margin-bottom: 0.5rem;
            margin-top: 1rem;
        }
        h4 {
            font-size: 13pt;
            font-weight: 600;
            color: #111827;
            margin-bottom: 0.5rem;
            margin-top: 0.75rem;
        }
        p {
            font-size: 11pt;
            line-height: 1.15;
            margin-bottom: 11pt;
            margin-top: 0;
            color: #111827;
        }
        ul {
            list-style-type: disc;
            margin-bottom: 11pt;
            margin-left: 1.5rem;
            padding-left: 0;
        }
        ol {
            list-style-type: decimal;
            margin-bottom: 11pt;
            margin-left: 1.5rem;
            padding-left: 0;
        }
        li {
            font-size: 11pt;
            line-height: 1.15;
            color: #111827;
            margin-bottom: 0;
        }
        blockquote {
            border-left: 4px solid #d1d5db;
            padding-left: 1rem;
            margin: 11pt 0;
            font-size: 11pt;
            color: #374151;
            font-style: italic;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
        }
        th, td {
            border: 1px solid #d1d5db;
            padding: 0.5rem 0.75rem;
            font-size: 11pt;
            color: #111827;
        }
        th {
            background-color: #f3f4f6;
            font-weight: 600;
        }
        img {
            max-width: 100%;
            height: auto;
            margin: 1rem 0;
        }
        strong {
            font-weight: 600;
            color: #111827;
        }
        em {
            font-style: italic;
        }
        hr {
            border: none;
            border-top: 1px solid #d1d5db;
            margin: 1rem 0;
        }
        """

    def _setup_custom_styles(self) -> None:
        """Crear estilos personalizados"""
        self.styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=self.styles["Heading1"],
                fontSize=18,
                textColor="#1a1a1a",
                spaceAfter=12,
                alignment=TA_CENTER,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="SubTitle",
                parent=self.styles["Heading2"],
                fontSize=14,
                textColor="#333333",
                spaceAfter=10,
                alignment=TA_LEFT,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="InfoText",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor="#666666",
                spaceAfter=6,
            )
        )

    async def generate_pdf(
        self,
        db: AsyncSession,
        combination: dict[str, Any],
        date_range: dict[str, str],
        chart_codes: list[CodigoGrafico] | None = None,
    ) -> bytes:
        """
        Genera un PDF para una combinación de filtros
        100% server-side con matplotlib + SVG del mapa

        Args:
            db: Sesión de base de datos
            combination: Combinación de filtros (grupo, eventos, clasificaciones)
            date_range: Rango de fechas
            chart_codes: Lista de códigos de charts a incluir

        Returns:
            Bytes del PDF generado
        """
        logger.info(
            f"Generando PDF server-side para {combination.get('group_name', 'Unknown')}"
        )

        # Charts por defecto si no se especifican
        if not chart_codes:
            chart_codes = [
                CodigoGrafico.CASOS_POR_SEMANA,
                CodigoGrafico.CORREDOR_ENDEMICO,
                CodigoGrafico.PIRAMIDE_EDAD,
                CodigoGrafico.MAPA_CHUBUT,
                CodigoGrafico.DISTRIBUCION_CLASIFICACION,
            ]

        # Crear PDF en memoria
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )

        # Contenido del PDF
        story = []

        # Portada
        story.extend(self._create_cover_page(combination, date_range))
        story.append(PageBreak())

        # Generar specs con datos reales
        generator = ChartSpecGenerator(db)

        # Convertir combinación a filtros
        filters = self._combination_to_filters(combination, date_range)

        # Generar cada chart
        for chart_code in chart_codes:
            try:
                logger.info(f"Generando chart: {chart_code}")

                # Generar spec con datos reales
                spec = await generator.generar_spec(
                    codigo_grafico=chart_code,
                    filtros=filters,
                    configuracion={"height": 400},
                )

                # Renderizar a imagen con alta resolución
                img_bytes = chart_renderer.renderizar_a_bytes(spec, dpi=300)

                # Agregar al PDF (SIN título ni descripción - ya están en la imagen)
                # story.append(Paragraph(spec.title, self.styles['SubTitle']))  # ELIMINADO
                # if spec.description:
                #     story.append(Paragraph(spec.description, self.styles['InfoText']))
                # story.append(Spacer(1, 0.2*inch))

                # Crear imagen de ReportLab
                img = Image(io.BytesIO(img_bytes), width=6.5 * inch, height=4 * inch)
                story.append(img)
                story.append(Spacer(1, 0.3 * inch))

                logger.info(f"Chart {chart_code} agregado al PDF")

            except Exception as e:
                logger.error(f"Error generando chart {chart_code}: {e}")
                # Agregar mensaje de error
                error_text = f"Error generando {chart_code}: {e!s}"
                story.append(Paragraph(error_text, self.styles["Normal"]))
                story.append(Spacer(1, 0.2 * inch))

        # Generar PDF
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        logger.info(f"PDF generado: {len(pdf_bytes)} bytes")
        return pdf_bytes

    def _create_cover_page(
        self, combination: dict[str, Any], date_range: dict[str, str]
    ) -> list:
        """Crea la portada del reporte"""
        story = []

        # Título principal
        story.append(Spacer(1, 1.5 * inch))
        story.append(Paragraph("Reporte Epidemiológico", self.styles["CustomTitle"]))
        story.append(Spacer(1, 0.3 * inch))

        # Subtítulo con nombre del grupo
        group_name = combination.get("group_name", "Sin especificar")
        story.append(Paragraph(group_name, self.styles["SubTitle"]))
        story.append(Spacer(1, 0.5 * inch))

        # Información del reporte
        info_lines = [
            f"<b>Período:</b> {date_range.get('from', '')} a {date_range.get('to', '')}",
            f"<b>Fecha de generación:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "<b>Provincia:</b> Chubut",
        ]

        # Agregar eventos si existen
        if combination.get("event_names"):
            events = ", ".join(combination["event_names"][:5])
            if len(combination["event_names"]) > 5:
                events += f" y {len(combination['event_names']) - 5} más"
            info_lines.append(f"<b>CasoEpidemiologicos:</b> {events}")

        # Agregar clasificaciones si existen
        if combination.get("clasificaciones"):
            clasif = ", ".join(combination["clasificaciones"])
            info_lines.append(f"<b>Clasificaciones:</b> {clasif}")

        for line in info_lines:
            story.append(Paragraph(line, self.styles["InfoText"]))
            story.append(Spacer(1, 0.1 * inch))

        story.append(Spacer(1, 1 * inch))

        # Pie de portada
        story.append(
            Paragraph(
                "Sistema de Vigilancia Epidemiológica<br/>Provincia del Chubut",
                self.styles["InfoText"],
            )
        )

        return story

    def _combination_to_filters(
        self, combination: dict[str, Any], date_range: dict[str, str]
    ) -> FiltrosGrafico:
        """Convierte combinación a FiltrosGrafico"""
        return FiltrosGrafico(
            ids_grupo_eno=[combination["group_id"]]
            if combination.get("group_id")
            else None,
            ids_tipo_eno=combination.get("event_ids"),
            clasificacion=combination.get("clasificaciones"),
            id_provincia=[26],  # Chubut por defecto
            fecha_desde=date_range.get("from"),
            fecha_hasta=date_range.get("to"),
        )

    async def generate_pdf_from_html(
        self,
        html_content: str,
        output_path: str,
        page_size: str = "A4",
        margin: str = "20mm",
        extra_css: str | None = None,
    ) -> None:
        """
        Convierte HTML enriquecido a PDF usando xhtml2pdf.
        Mantiene estilos inline e incrustaciones base64 de imágenes.
        """
        if not html_content:
            raise ValueError("No hay contenido HTML para generar el PDF")

        css = self._base_html_css.replace("A4", page_size).replace("20mm", margin)
        if extra_css:
            css = f"{css}\n{extra_css}"

        html_document = (
            "<!DOCTYPE html><html lang='es'><head><meta charset='utf-8'/>"
            f"<style>{css}</style></head><body>{html_content}</body></html>"
        )

        await asyncio.to_thread(self._write_pdf, html_document, output_path)

    def _write_pdf(self, html_document: str, output_path: str) -> None:
        from xhtml2pdf import pisa

        with open(output_path, "wb") as output_file:
            result = pisa.CreatePDF(html_document, dest=output_file)

        if result.err:
            raise RuntimeError("Error generando PDF a partir del HTML del boletín")


# Singleton instance
serverside_pdf_generator = ServerSidePDFGenerator()

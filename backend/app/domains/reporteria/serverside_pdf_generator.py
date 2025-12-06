"""
Server-Side PDF Generator
Genera PDFs 100% server-side con matplotlib + SVG rendering
Sin dependencias del frontend ni navegadores
"""

import asyncio
import io
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.charts.schemas import FiltrosGrafico
from app.domains.charts.services.renderer import chart_renderer
from app.domains.charts.services.spec_generator import ChartSpecGenerator

logger = logging.getLogger(__name__)


class ServerSidePDFGenerator:
    """
    Genera PDFs de reportes epidemiológicos 100% server-side
    Sin necesidad de navegador ni Playwright
    """

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self._base_html_css = """
        @page {
            size: A4;
            margin: 20mm;
        }
        body {
            font-family: 'Helvetica', 'Arial', sans-serif;
            color: #1f2937;
            line-height: 1.5;
            font-size: 11pt;
        }
        h1, h2, h3, h4 {
            color: #1e3a8a;
        }
        img {
            max-width: 100%;
            height: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
        }
        th, td {
            border: 1px solid #e5e7eb;
            padding: 0.35rem;
        }
        """

    def _setup_custom_styles(self):
        """Crear estilos personalizados"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor='#1a1a1a',
            spaceAfter=12,
            alignment=TA_CENTER
        ))

        self.styles.add(ParagraphStyle(
            name='SubTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor='#333333',
            spaceAfter=10,
            alignment=TA_LEFT
        ))

        self.styles.add(ParagraphStyle(
            name='InfoText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor='#666666',
            spaceAfter=6
        ))

    async def generate_pdf(
        self,
        db: AsyncSession,
        combination: Dict[str, Any],
        date_range: Dict[str, str],
        chart_codes: List[str] = None
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
        logger.info(f"Generando PDF server-side para {combination.get('group_name', 'Unknown')}")

        # Charts por defecto si no se especifican
        if not chart_codes:
            chart_codes = [
                "casos_por_semana",
                "corredor_endemico",
                "piramide_edad",
                "mapa_chubut",
                "distribucion_clasificacion",
            ]

        # Crear PDF en memoria
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
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
                    configuracion={"height": 400}
                )

                # Renderizar a imagen con alta resolución
                img_bytes = chart_renderer.renderizar_a_bytes(spec, dpi=300)

                # Agregar al PDF (SIN título ni descripción - ya están en la imagen)
                # story.append(Paragraph(spec.title, self.styles['SubTitle']))  # ELIMINADO
                # if spec.description:
                #     story.append(Paragraph(spec.description, self.styles['InfoText']))
                # story.append(Spacer(1, 0.2*inch))

                # Crear imagen de ReportLab
                img = Image(io.BytesIO(img_bytes), width=6.5*inch, height=4*inch)
                story.append(img)
                story.append(Spacer(1, 0.3*inch))

                logger.info(f"Chart {chart_code} agregado al PDF")

            except Exception as e:
                logger.error(f"Error generando chart {chart_code}: {e}")
                # Agregar mensaje de error
                error_text = f"Error generando {chart_code}: {str(e)}"
                story.append(Paragraph(error_text, self.styles['Normal']))
                story.append(Spacer(1, 0.2*inch))

        # Generar PDF
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        logger.info(f"PDF generado: {len(pdf_bytes)} bytes")
        return pdf_bytes

    def _create_cover_page(
        self,
        combination: Dict[str, Any],
        date_range: Dict[str, str]
    ) -> List:
        """Crea la portada del reporte"""
        story = []

        # Título principal
        story.append(Spacer(1, 1.5*inch))
        story.append(Paragraph(
            "Reporte Epidemiológico",
            self.styles['CustomTitle']
        ))
        story.append(Spacer(1, 0.3*inch))

        # Subtítulo con nombre del grupo
        group_name = combination.get('group_name', 'Sin especificar')
        story.append(Paragraph(
            group_name,
            self.styles['SubTitle']
        ))
        story.append(Spacer(1, 0.5*inch))

        # Información del reporte
        info_lines = [
            f"<b>Período:</b> {date_range.get('from', '')} a {date_range.get('to', '')}",
            f"<b>Fecha de generación:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "<b>Provincia:</b> Chubut",
        ]

        # Agregar eventos si existen
        if combination.get('event_names'):
            events = ', '.join(combination['event_names'][:5])
            if len(combination['event_names']) > 5:
                events += f" y {len(combination['event_names']) - 5} más"
            info_lines.append(f"<b>CasoEpidemiologicos:</b> {events}")

        # Agregar clasificaciones si existen
        if combination.get('clasificaciones'):
            clasif = ', '.join(combination['clasificaciones'])
            info_lines.append(f"<b>Clasificaciones:</b> {clasif}")

        for line in info_lines:
            story.append(Paragraph(line, self.styles['InfoText']))
            story.append(Spacer(1, 0.1*inch))

        story.append(Spacer(1, 1*inch))

        # Pie de portada
        story.append(Paragraph(
            "Sistema de Vigilancia Epidemiológica<br/>Provincia del Chubut",
            self.styles['InfoText']
        ))

        return story

    def _combination_to_filters(
        self,
        combination: Dict[str, Any],
        date_range: Dict[str, str]
    ) -> FiltrosGrafico:
        """Convierte combinación a FiltrosGrafico"""
        return FiltrosGrafico(
            ids_grupo_eno=[combination['group_id']] if combination.get('group_id') else None,
            ids_tipo_eno=combination.get('event_ids'),
            clasificacion=combination.get('clasificaciones'),
            id_provincia=[26],  # Chubut por defecto
            fecha_desde=date_range.get('from'),
            fecha_hasta=date_range.get('to'),
        )

    async def generate_pdf_from_html(
        self,
        html_content: str,
        output_path: str,
        page_size: str = "A4",
        margin: str = "20mm",
        extra_css: Optional[str] = None,
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

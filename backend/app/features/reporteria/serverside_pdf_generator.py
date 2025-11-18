"""
Server-Side PDF Generator
Genera PDFs 100% server-side con matplotlib + SVG rendering
Sin dependencias del frontend ni navegadores
"""

import io
import logging
from datetime import datetime
from typing import List, Dict, Any
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.chart_spec import ChartFilters
from app.services.chart_spec_generator import ChartSpecGenerator
from app.services.chart_renderer import chart_renderer

logger = logging.getLogger(__name__)


class ServerSidePDFGenerator:
    """
    Genera PDFs de reportes epidemiológicos 100% server-side
    Sin necesidad de navegador ni Playwright
    """

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

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
                spec = await generator.generate_spec(
                    chart_code=chart_code,
                    filters=filters,
                    config={"height": 400}
                )

                # Renderizar a imagen con alta resolución
                img_bytes = chart_renderer.render_to_bytes(spec, dpi=300)

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
            f"<b>Provincia:</b> Chubut",
        ]

        # Agregar eventos si existen
        if combination.get('event_names'):
            events = ', '.join(combination['event_names'][:5])
            if len(combination['event_names']) > 5:
                events += f" y {len(combination['event_names']) - 5} más"
            info_lines.append(f"<b>Eventos:</b> {events}")

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
    ) -> ChartFilters:
        """Convierte combinación a ChartFilters"""
        return ChartFilters(
            grupo_eno_ids=[combination['group_id']] if combination.get('group_id') else None,
            tipo_eno_ids=combination.get('event_ids'),
            clasificacion=combination.get('clasificaciones'),
            provincia_id=[26],  # Chubut por defecto
            fecha_desde=date_range.get('from'),
            fecha_hasta=date_range.get('to'),
        )


# Singleton instance
serverside_pdf_generator = ServerSidePDFGenerator()

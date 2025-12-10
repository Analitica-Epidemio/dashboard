"""
ZIP Report Generator
Generates multiple PDFs in parallel and packages them in a ZIP file
100% SERVER-SIDE - Sin Playwright
"""

import asyncio
import io
import logging
import zipfile
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.reporteria.serverside_pdf_generator import serverside_pdf_generator

logger = logging.getLogger(__name__)


class ZipReportGenerator:
    """
    Generates multiple PDF reports in parallel and packages them in a ZIP file
    """

    def __init__(self):
        pass

    async def generate_zip_report(
        self,
        db: AsyncSession,
        combinations: List[Dict[str, Any]],
        date_range: Dict[str, str],
        output_path: Optional[str] = None,
    ) -> bytes:
        """
        Generate multiple PDF reports in parallel and create a ZIP file
        100% SERVER-SIDE usando matplotlib + ReportLab

        Args:
            db: Database session
            combinations: List of filter combinations
            date_range: Date range for reports
            output_path: Optional path to save ZIP file

        Returns:
            ZIP file content as bytes
        """
        logger.info(
            f"Starting SERVER-SIDE ZIP report generation for {len(combinations)} combinations"
        )

        # Generate PDFs in parallel
        pdf_tasks = []
        for i, combo in enumerate(combinations):
            # Create task for PDF generation (server-side)
            task = self._generate_single_pdf(db, combo, date_range, i + 1)
            pdf_tasks.append(task)

        # Execute all PDF generations in parallel
        logger.info("Generating PDFs in parallel...")
        pdf_results = await asyncio.gather(*pdf_tasks, return_exceptions=True)

        # Create ZIP file
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Add metadata file
            metadata = self._create_metadata(combinations, date_range)
            zip_file.writestr("metadata.txt", metadata)

            # Add each PDF to ZIP
            successful_pdfs = 0
            for i, result in enumerate(pdf_results):
                combo = combinations[i]

                if isinstance(result, Exception):
                    logger.error(
                        f"Failed to generate PDF for combination {i + 1}: {result}"
                    )
                    # Add error file
                    error_msg = f"Error generando PDF para {combo.get('group_name', 'Unknown')}: {str(result)}"
                    zip_file.writestr(f"error_{i + 1:02d}.txt", error_msg)
                elif isinstance(result, bytes):
                    # Type narrowing: result is bytes here
                    if result:
                        # Generate filename
                        group_name = combo.get("group_name", f"Grupo_{i + 1}")
                        safe_name = self._safe_filename(group_name)
                        pdf_filename = f"{i + 1:02d}_{safe_name}.pdf"

                        zip_file.writestr(pdf_filename, result)
                        successful_pdfs += 1
                        logger.info(
                            f"Added {pdf_filename} to ZIP ({len(result)} bytes)"
                        )
                    else:
                        # Add empty file indicator
                        zip_file.writestr(
                            f"empty_{i + 1:02d}.txt",
                            "PDF generation returned empty content",
                        )

            logger.info(
                f"ZIP report completed: {successful_pdfs}/{len(combinations)} PDFs generated successfully"
            )

        zip_content = zip_buffer.getvalue()

        # Save to file if requested
        if output_path:
            with open(output_path, "wb") as f:
                f.write(zip_content)
            logger.info(f"ZIP report saved to {output_path}")

        return zip_content

    async def _generate_single_pdf(
        self,
        db: AsyncSession,
        combination: Dict[str, Any],
        date_range: Dict[str, str],
        index: int,
    ) -> bytes:
        """Generate a single PDF for a combination (SERVER-SIDE)"""
        try:
            logger.info(
                f"Generating SERVER-SIDE PDF {index} for {combination.get('group_name', 'Unknown')}"
            )

            pdf_content = await serverside_pdf_generator.generate_pdf(
                db=db, combination=combination, date_range=date_range
            )

            if pdf_content:
                logger.info(
                    f"SERVER-SIDE PDF {index} generated successfully ({len(pdf_content)} bytes)"
                )
                return pdf_content
            else:
                logger.warning(
                    f"SERVER-SIDE PDF {index} generation returned empty content"
                )
                return b""

        except Exception as e:
            logger.error(f"Error generating SERVER-SIDE PDF {index}: {e}")
            raise e

    def _safe_filename(self, name: str) -> str:
        """Convert name to safe filename"""
        # Remove/replace unsafe characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ "
        safe_name = "".join(c if c in safe_chars else "_" for c in name)

        # Replace multiple spaces/underscores with single underscore
        while "  " in safe_name:
            safe_name = safe_name.replace("  ", " ")
        while "__" in safe_name:
            safe_name = safe_name.replace("__", "_")

        safe_name = safe_name.replace(" ", "_").strip("_")

        # Limit length
        if len(safe_name) > 50:
            safe_name = safe_name[:50]

        return safe_name or "Unknown"

    def _create_metadata(
        self, combinations: List[Dict[str, Any]], date_range: Dict[str, str]
    ) -> str:
        """Create metadata text file content"""
        metadata_lines = [
            "REPORTE EPIDEMIOLÓGICO - METADATOS",
            "=" * 50,
            f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Período del reporte: {date_range.get('from', '')} a {date_range.get('to', '')}",
            f"Total de combinaciones: {len(combinations)}",
            "",
            "COMBINACIONES INCLUIDAS:",
            "-" * 30,
        ]

        for i, combo in enumerate(combinations, 1):
            metadata_lines.extend(
                [
                    f"{i:02d}. {combo.get('group_name', 'Sin nombre')}",
                    f"    ID: {combo.get('id', 'N/A')}",
                    f"    CasoEpidemiologicos: {', '.join(combo.get('event_names', [])) or 'Todos'}",
                    f"    Clasificaciones: {', '.join(combo.get('clasificaciones', [])) or 'Todas'}",
                    "",
                ]
            )

        metadata_lines.extend(
            [
                "",
                "ARCHIVOS INCLUIDOS:",
                "-" * 20,
                "- metadata.txt: Este archivo con información del reporte",
                "- XX_NombreGrupo.pdf: Reporte individual para cada combinación",
                "- error_XX.txt: Archivos de error (si los hay)",
                "",
                "Sistema de Vigilancia Epidemiológica - Provincia del Chubut",
            ]
        )

        return "\n".join(metadata_lines)


# Singleton instance
zip_generator = ZipReportGenerator()

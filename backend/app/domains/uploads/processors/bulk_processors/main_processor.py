"""Main orchestrator for all bulk processing operations."""

import logging
from typing import Dict, List

import pandas as pd

from .ciudadanos import CiudadanosBulkProcessor
from .diagnosticos import DiagnosticosBulkProcessor
from .establecimientos import EstablecimientosBulkProcessor
from .eventos import EventosBulkProcessor
from .investigaciones import InvestigacionesBulkProcessor
from .result import BulkOperationResult
from .salud import SaludBulkProcessor
from ..core.columns import Columns


class MainBulkProcessor:
    """
    Orchestrator principal que coordina todos los bulk processors.

    Sigue el orden correcto de procesamiento para respetar las dependencias:
    1. Establecimientos (catálogo independiente)
    2. Ciudadanos (datos base de personas)
    3. Eventos (requiere ciudadanos y establecimientos)
    4. Todo lo demás (requiere eventos)
    """

    def __init__(self, context, logger: logging.Logger):
        self.context = context
        self.logger = logger

        # Inicializar todos los processors
        self.establecimientos_processor = EstablecimientosBulkProcessor(context, logger)
        self.ciudadanos_processor = CiudadanosBulkProcessor(context, logger)
        self.eventos_processor = EventosBulkProcessor(context, logger)
        self.salud_processor = SaludBulkProcessor(context, logger)
        self.diagnosticos_processor = DiagnosticosBulkProcessor(context, logger)
        self.investigaciones_processor = InvestigacionesBulkProcessor(context, logger)

    def process_all(self, df: pd.DataFrame) -> Dict[str, BulkOperationResult]:
        """
        Procesar todos los datos en el orden correcto.

        Returns:
            Dict con los resultados de cada operación bulk
        """
        results = {}

        self.logger.info("Iniciando procesamiento bulk completo")

        # 1. ESTABLECIMIENTOS - Independientes, crean el catálogo
        self.logger.info("=== Paso 1: Establecimientos ===")
        establecimiento_mapping = (
            self.establecimientos_processor.bulk_upsert_establecimientos(df)
        )
        self.logger.info(f"Procesados {len(establecimiento_mapping)} establecimientos")

        # 2. CIUDADANOS - Datos base de personas
        self.logger.info("=== Paso 2: Ciudadanos ===")
        results["ciudadanos"] = self.ciudadanos_processor.bulk_upsert_ciudadanos(df)
        self.logger.info(
            f"Ciudadanos: {results['ciudadanos'].inserted_count} insertados"
        )

        # Only process domicilios if required columns are present
        if Columns.CALLE_DOMICILIO in df.columns:
            results["domicilios"] = (
                self.ciudadanos_processor.bulk_upsert_ciudadanos_domicilios(df)
            )
            self.logger.info(
                f"Domicilios: {results['domicilios'].inserted_count} insertados"
            )
        else:
            self.logger.info(
                "Skipping domicilios processing - no address columns found"
            )

        # Only process viajes if required columns are present
        if Columns.PAIS_VIAJE in df.columns:
            results["viajes"] = self.ciudadanos_processor.bulk_upsert_viajes(df)
            self.logger.info(f"Viajes: {results['viajes'].inserted_count} insertados")
        else:
            self.logger.info("Skipping viajes processing - no travel columns found")

        # Only process comorbilidades if required columns are present
        if Columns.COMORBILIDAD in df.columns:
            results["comorbilidades"] = (
                self.ciudadanos_processor.bulk_upsert_comorbilidades(df)
            )
            self.logger.info(
                f"Comorbilidades: {results['comorbilidades'].inserted_count} insertados"
            )
        else:
            self.logger.info(
                "Skipping comorbilidades processing - no comorbidity columns found"
            )

        # 3. EVENTOS - Requiere ciudadanos y establecimientos
        self.logger.info("=== Paso 3: Eventos ===")

        # IMPORTANTE: Crear síntomas ANTES de crear eventos y relaciones
        sintomas_mapping = self.eventos_processor._get_or_create_sintomas(df)
        self.logger.info(f"Creados/verificados {len(sintomas_mapping)} síntomas")

        evento_mapping = self.eventos_processor.bulk_upsert_eventos(
            df, establecimiento_mapping
        )
        self.logger.info(f"Procesados {len(evento_mapping)} eventos")

        results["ciudadanos_datos"] = (
            self.ciudadanos_processor.bulk_upsert_ciudadanos_datos(df, evento_mapping)
        )
        self.logger.info(
            f"Datos ciudadanos: {results['ciudadanos_datos'].inserted_count} insertados"
        )

        # Only process ámbitos if required columns are present
        if Columns.TIPO_LUGAR_OCURRENCIA in df.columns:
            results["ambitos_concurrencia"] = (
                self.eventos_processor.bulk_upsert_ambitos_concurrencia(df)
            )
            self.logger.info(
                f"Ámbitos concurrencia: {results['ambitos_concurrencia'].inserted_count} insertados"
            )
        else:
            self.logger.info("Skipping ámbitos processing - no location columns found")

        results["sintomas_eventos"] = (
            self.eventos_processor.bulk_upsert_sintomas_eventos(df, sintomas_mapping)
        )
        self.logger.info(
            f"Síntomas eventos: {results['sintomas_eventos'].inserted_count} insertados"
        )

        results["antecedentes_eventos"] = (
            self.eventos_processor.bulk_upsert_antecedentes_epidemiologicos(df)
        )
        self.logger.info(
            f"Antecedentes epidemiológicos: {results['antecedentes_eventos'].inserted_count} insertados"
        )

        # 4. SALUD - Muestras y vacunas (requiere eventos)
        self.logger.info("=== Paso 4: Salud ===")
        results["muestras_eventos"] = self.salud_processor.bulk_upsert_muestras_eventos(
            df
        )
        self.logger.info(
            f"Muestras eventos: {results['muestras_eventos'].inserted_count} insertados"
        )

        results["vacunas_ciudadanos"] = (
            self.salud_processor.bulk_upsert_vacunas_ciudadanos(df)
        )
        self.logger.info(
            f"Vacunas ciudadanos: {results['vacunas_ciudadanos'].inserted_count} insertados"
        )

        # 5. DIAGNÓSTICOS - Requiere eventos
        self.logger.info("=== Paso 5: Diagnósticos ===")
        results["diagnosticos_eventos"] = (
            self.diagnosticos_processor.bulk_upsert_diagnosticos_eventos(df)
        )
        self.logger.info(
            f"Diagnósticos eventos: {results['diagnosticos_eventos'].inserted_count} insertados"
        )

        results["estudios_eventos"] = (
            self.diagnosticos_processor.bulk_upsert_estudios_eventos(df)
        )
        self.logger.info(
            f"Estudios eventos: {results['estudios_eventos'].inserted_count} insertados"
        )

        results["tratamientos_eventos"] = (
            self.diagnosticos_processor.bulk_upsert_tratamientos_eventos(df)
        )
        self.logger.info(
            f"Tratamientos eventos: {results['tratamientos_eventos'].inserted_count} insertados"
        )

        results["internaciones_eventos"] = (
            self.diagnosticos_processor.bulk_upsert_internaciones_eventos(df)
        )
        self.logger.info(
            f"Internaciones eventos: {results['internaciones_eventos'].inserted_count} insertados"
        )

        # 6. INVESTIGACIONES - Requiere eventos
        self.logger.info("=== Paso 6: Investigaciones ===")
        results["investigaciones_eventos"] = (
            self.investigaciones_processor.bulk_upsert_investigaciones_eventos(df)
        )
        self.logger.info(
            f"Investigaciones eventos: {results['investigaciones_eventos'].inserted_count} insertados"
        )

        results["contactos_notificaciones"] = (
            self.investigaciones_processor.bulk_upsert_contactos_notificaciones(df)
        )
        self.logger.info(
            f"Contactos notificaciones: {results['contactos_notificaciones'].inserted_count} insertados"
        )

        self.logger.info("=== Procesamiento bulk completado ===")
        self._log_summary(results)

        return results

    def _log_summary(self, results: Dict[str, BulkOperationResult]) -> None:
        """Log a summary of all bulk operations."""
        total_inserted = sum(r.inserted_count for r in results.values())
        total_errors = sum(len(r.errors) for r in results.values())
        total_duration = sum(r.duration_seconds for r in results.values())

        self.logger.info("=== RESUMEN FINAL ===")
        self.logger.info(f"Total registros insertados: {total_inserted}")
        self.logger.info(f"Total errores: {total_errors}")
        self.logger.info(f"Tiempo total: {total_duration:.2f} segundos")

        if total_errors > 0:
            self.logger.warning("Errores encontrados:")
            for operation_name, result in results.items():
                if result.errors:
                    self.logger.warning(
                        f"{operation_name}: {len(result.errors)} errores"
                    )
                    for error in result.errors[:3]:  # Solo mostrar los primeros 3
                        self.logger.warning(f"  - {error}")
                    if len(result.errors) > 3:
                        self.logger.warning(
                            f"  ... y {len(result.errors) - 3} errores más"
                        )

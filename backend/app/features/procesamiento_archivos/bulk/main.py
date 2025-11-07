"""
Main orchestrator for all bulk processing operations.

Coordina el procesamiento de todos los dominios en el orden correcto.
"""

import logging
from typing import Dict

import pandas as pd

from ..config.columns import Columns
from .ciudadanos import CiudadanosManager
from .diagnosticos import DiagnosticosProcessor
from .establecimientos import EstablecimientosProcessor
from .eventos import EventosManager
from .investigaciones import InvestigacionesProcessor
from .salud import SaludManager
from .shared import BulkOperationResult


class MainProcessor:
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

        # Initialize all managers and processors
        self.establecimientos_processor = EstablecimientosProcessor(context, logger)
        self.ciudadanos_manager = CiudadanosManager(context, logger)
        self.eventos_manager = EventosManager(context, logger)
        self.salud_manager = SaludManager(context, logger)
        self.diagnosticos_processor = DiagnosticosProcessor(context, logger)
        self.investigaciones_processor = InvestigacionesProcessor(context, logger)

        # Progress tracking: ~18 operaciones totales
        self.total_operations = 18
        self.completed_operations = 0

    def _update_operation_progress(self, operation_name: str):
        """Actualiza progreso después de cada operación."""
        self.completed_operations += 1
        percentage = int((self.completed_operations / self.total_operations) * 100)

        if self.context.progress_callback:
            self.context.progress_callback(percentage, f"Guardando {operation_name}")

    def process_all(self, df: pd.DataFrame) -> Dict[str, BulkOperationResult]:
        """
        Procesar todos los datos en el orden correcto.

        IMPORTANTE: Cada operación hace COMMIT inmediato para persistir datos
        y evitar perder todo si algo falla después.

        Returns:
            Dict con los resultados de cada operación bulk
        """
        results = {}

        # 1. ESTABLECIMIENTOS - Independientes, crean el catálogo
        establecimiento_mapping = (
            self.establecimientos_processor.upsert_establecimientos(df)
        )
        self.context.session.commit()  # COMMIT inmediato
        self.logger.info(f"✅ Establecimientos committed")
        self._update_operation_progress("establecimientos")

        # Ensure "Desconocido" establishment exists (used as default by muestras)
        from app.domains.territorio.establecimientos_models import Establecimiento
        from sqlalchemy import select
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from .shared import get_current_timestamp

        if "DESCONOCIDO" not in establecimiento_mapping:
            stmt = pg_insert(Establecimiento.__table__).values(
                {
                    "nombre": "Desconocido",
                    "created_at": get_current_timestamp(),
                    "updated_at": get_current_timestamp(),
                }
            )
            self.context.session.execute(stmt.on_conflict_do_nothing())

            stmt = (
                select(Establecimiento.id)
                .where(Establecimiento.nombre == "Desconocido")
                .limit(1)
            )
            desconocido_id = self.context.session.execute(stmt).scalar()
            if desconocido_id:
                establecimiento_mapping["DESCONOCIDO"] = desconocido_id

        # 2. CIUDADANOS - Base citizen data
        results["ciudadanos"] = self.ciudadanos_manager.upsert_ciudadanos(df)
        self.context.session.commit()  # COMMIT inmediato
        self.logger.info(f"✅ Ciudadanos committed")
        self._update_operation_progress("ciudadanos")

        # Only process domicilios if required columns are present
        if Columns.CALLE_DOMICILIO.name in df.columns:
            results["domicilios"] = (
                self.ciudadanos_manager.upsert_ciudadanos_domicilios(df)
            )
            self.context.session.commit()  # COMMIT inmediato
            self.logger.info(f"✅ Domicilios committed")
            self._update_operation_progress("domicilios")

        # Only process viajes if required columns are present
        if Columns.PAIS_VIAJE in df.columns:
            results["viajes"] = self.ciudadanos_manager.upsert_viajes(df)
            self.context.session.commit()  # COMMIT inmediato
            self.logger.info(f"✅ Viajes committed")
            self._update_operation_progress("viajes")

        # Only process comorbilidades if required columns are present
        if Columns.COMORBILIDAD in df.columns:
            results["comorbilidades"] = self.ciudadanos_manager.upsert_comorbilidades(
                df
            )
            self.context.session.commit()  # COMMIT inmediato
            self.logger.info(f"✅ Comorbilidades committed")
            self._update_operation_progress("comorbilidades")

        # 3. EVENTOS - Requires ciudadanos and establecimientos
        # IMPORTANT: Create symptoms BEFORE creating events and relationships
        sintomas_mapping = self.eventos_manager._get_or_create_sintomas(df)

        evento_mapping = self.eventos_manager.upsert_eventos(
            df, establecimiento_mapping
        )
        self.context.session.commit()  # COMMIT inmediato - eventos son críticos
        self.logger.info(f"✅ Eventos committed")
        self._update_operation_progress("eventos")

        results["ciudadanos_datos"] = self.ciudadanos_manager.upsert_ciudadanos_datos(
            df, evento_mapping
        )
        self.context.session.commit()  # COMMIT inmediato
        self.logger.info(f"✅ Ciudadanos datos committed")
        self._update_operation_progress("datos de ciudadanos")

        # Only process ámbitos if required columns are present
        if Columns.TIPO_LUGAR_OCURRENCIA in df.columns:
            results["ambitos_concurrencia"] = (
                self.eventos_manager.upsert_ambitos_concurrencia(df, evento_mapping)
            )
            self.context.session.commit()  # COMMIT inmediato
            self.logger.info(f"✅ Ambitos committed")
            self._update_operation_progress("ámbitos de concurrencia")

        results["sintomas_eventos"] = self.eventos_manager.upsert_sintomas_eventos(
            df, sintomas_mapping, evento_mapping
        )
        self.context.session.commit()  # COMMIT inmediato
        self.logger.info(f"✅ Síntomas eventos committed")
        self._update_operation_progress("síntomas")

        results["antecedentes_eventos"] = (
            self.eventos_manager.upsert_antecedentes_epidemiologicos(df, evento_mapping)
        )
        self.context.session.commit()  # COMMIT inmediato
        self.logger.info(f"✅ Antecedentes committed")
        self._update_operation_progress("antecedentes epidemiológicos")

        # 4. SALUD - Samples and vaccines (requires events)
        results["muestras_eventos"] = self.salud_manager.upsert_muestras_eventos(
            df, establecimiento_mapping, evento_mapping
        )
        self.context.session.commit()  # COMMIT inmediato
        self.logger.info(f"✅ Muestras eventos committed")
        self._update_operation_progress("muestras")

        results["vacunas_ciudadanos"] = self.salud_manager.upsert_vacunas_ciudadanos(
            df, evento_mapping
        )
        self.context.session.commit()  # COMMIT inmediato
        self.logger.info(f"✅ Vacunas committed")
        self._update_operation_progress("vacunas")

        # 5. DIAGNOSTICS - Requires events
        results["diagnosticos_eventos"] = (
            self.diagnosticos_processor.upsert_diagnosticos_eventos(df, evento_mapping)
        )
        self.context.session.commit()  # COMMIT inmediato
        self.logger.info(f"✅ Diagnósticos committed")
        self._update_operation_progress("diagnósticos")

        results["estudios_eventos"] = (
            self.diagnosticos_processor.upsert_estudios_eventos(df, evento_mapping)
        )
        self.context.session.commit()  # COMMIT inmediato
        self.logger.info(f"✅ Estudios committed")
        self._update_operation_progress("estudios clínicos")

        results["tratamientos_eventos"] = (
            self.diagnosticos_processor.upsert_tratamientos_eventos(df, evento_mapping)
        )
        self.context.session.commit()  # COMMIT inmediato
        self.logger.info(f"✅ Tratamientos committed")
        self._update_operation_progress("tratamientos")

        results["internaciones_eventos"] = (
            self.diagnosticos_processor.upsert_internaciones_eventos(df, evento_mapping)
        )
        self.context.session.commit()  # COMMIT inmediato
        self.logger.info(f"✅ Internaciones committed")
        self._update_operation_progress("internaciones")

        # 6. INVESTIGACIONES - Requiere eventos
        results["investigaciones_eventos"] = (
            self.investigaciones_processor.upsert_investigaciones_eventos(
                df, evento_mapping
            )
        )
        self.context.session.commit()  # COMMIT inmediato
        self.logger.info(f"✅ Investigaciones committed")
        self._update_operation_progress("investigaciones")

        results["contactos_notificaciones"] = (
            self.investigaciones_processor.upsert_contactos_notificaciones(df)
        )
        self.context.session.commit()  # COMMIT inmediato
        self.logger.info(f"✅ Contactos committed")
        self._update_operation_progress("contactos y notificaciones")
        self._log_summary(results)

        return results

    def _log_summary(self, results: Dict[str, BulkOperationResult]) -> None:
        """Log a summary of all bulk operations."""
        total_inserted = sum(r.inserted_count for r in results.values())
        total_errors = sum(len(r.errors) for r in results.values())
        total_duration = sum(r.duration_seconds for r in results.values())

        self.logger.info(
            f"Bulk processing completed: {total_inserted} records in {total_duration:.2f}s"
        )

        if total_errors > 0:
            self.logger.warning(f"Total errors: {total_errors}")
            for operation_name, result in results.items():
                if result.errors:
                    self.logger.warning(
                        f"{operation_name}: {len(result.errors)} errors"
                    )
                    # Log primeros 2 errores para debug
                    for error in result.errors[:2]:
                        self.logger.warning(f"  - {error}")

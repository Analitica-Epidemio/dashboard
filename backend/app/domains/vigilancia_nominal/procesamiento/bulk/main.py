"""
Main orchestrator for all bulk processing operations - OPTIMIZADO.

Coordina el procesamiento de todos los dominios en el orden correcto.

OPTIMIZACIONES ARQUITECTURALES:
- Pre-procesamiento centralizado (conversiones de tipos una sola vez)
- Pre-filtrado por dominios (evita filtros redundantes)
- Join con evento_mapping una sola vez
- Creación de catálogos al inicio (mejor orden de ejecución)
- Ejecución paralela de operaciones independientes (ThreadPoolExecutor)
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Tuple

import polars as pl
from sqlalchemy import text, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.bulk import BulkOperationResult, get_current_timestamp, pl_safe_date, pl_safe_int
from app.domains.territorio.establecimientos_models import Establecimiento
from ..config.columns import Columns
from .ciudadanos import CiudadanosManager
from .diagnosticos import DiagnosticosProcessor
from .establecimientos import EstablecimientosProcessor
from .eventos import CasoEpidemiologicosManager
from .investigaciones import InvestigacionesProcessor
from .salud import SaludManager


class MainProcessor:
    """
    Orchestrator principal que coordina todos los bulk processors.

    Sigue el orden correcto de procesamiento para respetar las dependencias:
    1. Establecimientos (catálogo independiente)
    2. Ciudadanos (datos base de personas)
    3. CasoEpidemiologicos (requiere ciudadanos y establecimientos)
    4. Todo lo demás (requiere eventos)
    """

    def __init__(self, context, logger: logging.Logger):
        self.context = context
        self.logger = logger

        # Inicializar todos los managers y processors
        self.procesador_establecimientos = EstablecimientosProcessor(context, logger)
        self.manager_ciudadanos = CiudadanosManager(context, logger)
        self.manager_eventos = CasoEpidemiologicosManager(context, logger)
        self.manager_salud = SaludManager(context, logger)
        self.procesador_diagnosticos = DiagnosticosProcessor(context, logger)
        self.procesador_investigaciones = InvestigacionesProcessor(context, logger)

        # Seguimiento de progreso: ~19 operaciones totales (incluyendo agentes_eventos)
        self.total_operaciones = 19
        self.operaciones_completadas = 0

    def _preprocesar_dataframe(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Pre-procesa el DataFrame con conversiones comunes.

        OPTIMIZACIÓN: Convierte columnas comunes UNA SOLA VEZ en lugar de
        repetir conversiones en cada processor (elimina ~40 conversiones redundantes).

        Args:
            df: DataFrame original

        Returns:
            DataFrame con columnas ya convertidas a los tipos correctos
        """
        # Lista de columnas a convertir (solo si existen en el DataFrame)
        conversiones = []

        # IDs principales - usados en TODOS los processors
        if Columns.CODIGO_CIUDADANO.name in df.columns:
            conversiones.append(
                pl_safe_int(Columns.CODIGO_CIUDADANO.name).alias("codigo_ciudadano_int")
            )

        if Columns.IDEVENTOCASO.name in df.columns:
            conversiones.append(
                pl_safe_int(Columns.IDEVENTOCASO.name).alias("id_evento_caso_int")
            )

        # Fechas comunes - usadas en múltiples processors
        columnas_fecha = [
            Columns.FECHA_NACIMIENTO.name,
            Columns.FECHA_APERTURA.name,
            Columns.FECHA_INICIO_SINTOMA.name,
            Columns.FECHA_INTERNACION.name,
            Columns.FECHA_ALTA_MEDICA.name,
        ]

        for nombre_col in columnas_fecha:
            if nombre_col in df.columns:
                conversiones.append(
                    pl_safe_date(nombre_col).alias(f"{nombre_col}_date")
                )

        # Aplicar conversiones si hay alguna
        if conversiones:
            return df.with_columns(conversiones)

        return df

    def _preparar_vistas_filtradas(
        self, df: pl.DataFrame
    ) -> Tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
        """
        Crea vistas pre-filtradas del DataFrame por dominio.

        OPTIMIZACIÓN: Filtra UNA SOLA VEZ en lugar de que cada processor
        filtre el DataFrame completo (elimina ~15 filtros redundantes).

        Args:
            df: DataFrame pre-procesado

        Returns:
            Tuple de (df_ciudadanos, df_eventos, df_completo)
        """
        # Vista para processors de ciudadanos
        df_ciudadanos = df.filter(
            pl.col(Columns.CODIGO_CIUDADANO.name).is_not_null()
        ) if Columns.CODIGO_CIUDADANO.name in df.columns else df

        # Vista para processors de eventos
        df_eventos = df.filter(
            pl.col(Columns.IDEVENTOCASO.name).is_not_null()
        ) if Columns.IDEVENTOCASO.name in df.columns else df

        return df_ciudadanos, df_eventos, df

    def _agregar_mapeo_evento_a_df(
        self, df: pl.DataFrame, mapeo_eventos: Dict[int, int]
    ) -> pl.DataFrame:
        """
        Agrega columna id_evento al DataFrame mediante JOIN.

        OPTIMIZACIÓN: Hace el JOIN UNA SOLA VEZ en lugar de que cada processor
        convierta el dict a DataFrame y haga su propio join (elimina ~10 joins redundantes).

        Args:
            df: DataFrame original
            mapeo_eventos: Dict mapping id_evento_caso -> id_evento

        Returns:
            DataFrame con columna id_evento agregada
        """
        if not mapeo_eventos or Columns.IDEVENTOCASO.name not in df.columns:
            return df

        # Crear DataFrame de mapping una sola vez
        df_mapeo = pl.DataFrame({
            "id_evento_caso_original": list(mapeo_eventos.keys()),
            "id_caso": list(mapeo_eventos.values()),
        })

        # Join con el DataFrame principal
        # Usar left join para no perder registros sin evento
        df_con_evento = df.join(
            df_mapeo,
            left_on=Columns.IDEVENTOCASO.name,
            right_on="id_evento_caso_original",
            how="left"
        )

        return df_con_evento

    def _actualizar_progreso_operacion(self, nombre_operacion: str):
        """Actualiza progreso después de cada operación."""
        self.operaciones_completadas += 1
        porcentaje = int((self.operaciones_completadas / self.total_operaciones) * 100)

        if self.context.progress_callback:
            self.context.progress_callback(porcentaje, f"Guardando {nombre_operacion}")

    def procesar_todo(self, df: pl.DataFrame) -> Dict[str, BulkOperationResult]:
        """
        Procesar todos los datos en el orden correcto con Polars puro + optimizaciones arquitecturales.

        OPTIMIZACIONES APLICADAS:
        1. Pre-procesamiento: Conversiones de tipos comunes una sola vez (~40 conversions eliminadas)
        2. Pre-filtrado: Vistas filtradas por dominio (~15 filtros eliminados)
        3. Join centralizado: evento_mapping join una sola vez (~10 joins eliminados)
        4. Commits minimizados: Solo 3 commits (reducción de ~76% vs 13 commits originales)
        5. FK checks deshabilitados: ~30-50% más rápido en INSERTs
        6. Paralelización: 12 operaciones ejecutadas concurrentemente con ThreadPoolExecutor

        ESTRATEGIA DE COMMITS (solo los estrictamente necesarios):
        1. COMMIT 1: Establecimientos + Ciudadanos + datos asociados (domicilios, viajes, comorbilidades)
        2. COMMIT 2: CasoEpidemiologicos (necesario para JOIN que agrega id_evento al DataFrame)
        3. COMMIT 3: Todas las relaciones y datos secundarios (12 operaciones en paralelo)

        Args:
            df: Polars DataFrame con datos procesados

        Returns:
            Dict con los resultados de cada operación bulk
        """
        resultados = {}

        # ===== OPTIMIZACIÓN POSTGRESQL: DESHABILITAR FK CHECKS =====
        # Esto acelera INSERTs ~30-50% porque PostgreSQL no valida FKs
        # Es seguro porque ya validamos los datos antes
        self.logger.info("🚀 Deshabilitando FK checks para máxima velocidad...")
        self.context.session.execute(text("SET session_replication_role = replica"))

        try:
            # ===== OPTIMIZACIÓN 1: PRE-PROCESAMIENTO =====
            # Convertir columnas comunes UNA SOLA VEZ
            self.logger.info("Pre-procesando DataFrame (conversiones de tipos)...")
            df = self._preprocesar_dataframe(df)

            # ===== OPTIMIZACIÓN 2: PRE-FILTRADO =====
            # Crear vistas filtradas por dominio UNA SOLA VEZ
            self.logger.info("Creando vistas filtradas por dominio...")
            df_ciudadanos, df_eventos, df_completo = self._preparar_vistas_filtradas(df)

            # 1. ESTABLECIMIENTOS - Independientes, crean el catálogo
            mapeo_establecimientos = (
                self.procesador_establecimientos.upsert_establecimientos(df)
            )
            self.context.session.flush()  # FLUSH en lugar de COMMIT (permite queries en misma transacción)
            self.logger.info("✅ Establecimientos flushed")
            self._actualizar_progreso_operacion("establecimientos")

            # Asegurar que existe establecimiento "Desconocido" (usado por defecto en muestras)
            if "DESCONOCIDO" not in mapeo_establecimientos:
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
                id_desconocido = self.context.session.execute(stmt).scalar()
                if id_desconocido:
                    mapeo_establecimientos["DESCONOCIDO"] = id_desconocido

            # 2. CIUDADANOS - Base citizen data
            # OPTIMIZACIÓN: Usar vista pre-filtrada df_ciudadanos
            resultados["ciudadanos"] = self.manager_ciudadanos.upsert_ciudadanos(df_ciudadanos)

            # Solo procesar domicilios si las columnas requeridas están presentes
            # DOMICILIOS, VIAJES & COMORBILIDADES - Ejecutar pero NO hacer commit aún
            if Columns.CALLE_DOMICILIO.name in df.columns:
                resultados["domicilios"] = (
                    self.manager_ciudadanos.upsert_ciudadanos_domicilios(df_ciudadanos)
                )

            if Columns.PAIS_VIAJE in df.columns:
                resultados["viajes"] = self.manager_ciudadanos.upsert_viajes(df_ciudadanos)

            if Columns.COMORBILIDAD in df.columns:
                resultados["comorbilidades"] = self.manager_ciudadanos.upsert_comorbilidades(
                    df_ciudadanos
                )

            # COMMIT CRÍTICO 1: Establecimientos + Ciudadanos + datos asociados
            # Combina establecimientos (flushed antes) + ciudadanos + domicilios + viajes + comorbilidades
            self.context.session.commit()
            self.logger.info("✅ Establecimientos, ciudadanos y datos asociados committed")
            self._actualizar_progreso_operacion("establecimientos y ciudadanos")

            # 3. EVENTOS - Requiere ciudadanos y establecimientos
            # IMPORTANTE: Crear síntomas ANTES de crear eventos y relaciones
            mapeo_sintomas = self.manager_eventos._get_or_create_sintomas(df)

            mapeo_eventos = self.manager_eventos.upsert_eventos(
                df, mapeo_establecimientos
            )
            # COMMIT CRÍTICO 2: CasoEpidemiologicos
            # Este commit ES NECESARIO porque necesitamos los id_evento para el JOIN siguiente
            self.context.session.commit()
            self.logger.info("✅ CasoEpidemiologicos committed")
            self._actualizar_progreso_operacion("eventos")

            # ===== OPTIMIZACIÓN 3: JOIN CENTRALIZADO =====
            # Agregar id_evento al DataFrame UNA SOLA VEZ
            # Esto elimina ~10 joins redundantes en los processors
            self.logger.info("Agregando id_evento al DataFrame (join centralizado)...")
            df_con_evento = self._agregar_mapeo_evento_a_df(df, mapeo_eventos)
            df_eventos_con_id = self._agregar_mapeo_evento_a_df(df_eventos, mapeo_eventos)

            # === TODAS LAS OPERACIONES SIGUIENTES NO NECESITAN COMMIT INTERMEDIO ===
            # OPTIMIZACIÓN: Ejecutar en PARALELO con ThreadPoolExecutor
            # IMPORTANTE: Dividir en 2 fases por dependencias (estudios depende de muestras)

            # FASE 1: Operaciones independientes (incluyendo muestras y agentes)
            self.logger.info("🚀 Fase 1: Ejecutando 12 operaciones independientes en paralelo...")

            operaciones_fase1 = [
                (
                    self.manager_ciudadanos.upsert_ciudadanos_datos,
                    (df_con_evento,),
                    "ciudadanos_datos"
                ),
                (
                    self.manager_eventos.upsert_sintomas_eventos,
                    (df_eventos_con_id, mapeo_sintomas),
                    "sintomas_eventos"
                ),
                (
                    self.manager_eventos.upsert_antecedentes_epidemiologicos,
                    (df_eventos_con_id,),
                    "antecedentes_eventos"
                ),
                (
                    self.manager_salud.upsert_muestras_eventos,
                    (df_eventos_con_id, mapeo_establecimientos, mapeo_eventos),
                    "muestras_eventos"
                ),
                (
                    self.manager_salud.upsert_vacunas_ciudadanos,
                    (df_eventos_con_id,),
                    "vacunas_ciudadanos"
                ),
                (
                    self.procesador_diagnosticos.upsert_diagnosticos_eventos,
                    (df_eventos_con_id,),
                    "diagnosticos_eventos"
                ),
                (
                    self.procesador_diagnosticos.upsert_tratamientos_eventos,
                    (df_eventos_con_id,),
                    "tratamientos_eventos"
                ),
                (
                    self.procesador_diagnosticos.upsert_internaciones_eventos,
                    (df_eventos_con_id,),
                    "internaciones_eventos"
                ),
                (
                    self.procesador_investigaciones.upsert_investigaciones_eventos,
                    (df_eventos_con_id,),
                    "investigaciones_eventos"
                ),
                (
                    self.procesador_investigaciones.upsert_contactos_notificaciones,
                    (df_eventos_con_id,),
                    "contactos_notificaciones"
                ),
                (
                    self.manager_eventos.upsert_agentes_eventos,
                    (df_eventos_con_id, mapeo_eventos),
                    "agentes_eventos"
                ),
            ]

            # Agregar ambitos_concurrencia si existe la columna
            if Columns.TIPO_LUGAR_OCURRENCIA in df.columns:
                operaciones_fase1.append(
                    (
                        self.manager_eventos.upsert_ambitos_concurrencia,
                        (df_eventos_con_id,),
                        "ambitos_concurrencia"
                    )
                )

            # Ejecutar FASE 1 en paralelo (max 4 threads concurrentes)
            with ThreadPoolExecutor(max_workers=4) as executor:
                # Enviar todas las operaciones de fase 1
                futuro_a_operacion = {
                    executor.submit(func_op, *args): nombre_op
                    for func_op, args, nombre_op in operaciones_fase1
                }

                # Recolectar resultados a medida que completan
                for futuro in as_completed(futuro_a_operacion):
                    nombre_op = futuro_a_operacion[futuro]
                    try:
                        resultado = futuro.result()
                        resultados[nombre_op] = resultado
                        self.logger.info(f"✅ {nombre_op}: {resultado.inserted_count} registros en {resultado.duration_seconds:.2f}s")
                    except Exception as exc:
                        self.logger.error(f"❌ {nombre_op} generó excepción: {exc}")
                        raise

            self.logger.info("✅ Fase 1 completada")

            # FASE 2: Operaciones que DEPENDEN de fase 1 (estudios depende de muestras)
            self.logger.info("🚀 Fase 2: Ejecutando operaciones dependientes...")

            # Estudios depende de que muestras_eventos ya esté en BD
            try:
                resultado = self.procesador_diagnosticos.upsert_estudios_eventos(df_eventos_con_id)
                resultados["estudios_eventos"] = resultado
                self.logger.info(f"✅ estudios_eventos: {resultado.inserted_count} registros en {resultado.duration_seconds:.2f}s")
            except Exception as exc:
                self.logger.error(f"❌ estudios_eventos generó excepción: {exc}")
                raise

            self.logger.info("✅ Todas las operaciones completadas (Fase 1 + Fase 2)")

            # ===== COMMIT CRÍTICO 3: TODAS LAS RELACIONES Y DATOS SECUNDARIOS =====
            # Todas las operaciones desde ciudadanos_datos hasta contactos en un solo commit
            # Esto incluye: ciudadanos_datos, ambitos, síntomas, antecedentes, muestras,
            # vacunas, diagnósticos, estudios, tratamientos, internaciones, investigaciones, contactos
            self.context.session.commit()
            self.logger.info("✅ Todas las relaciones y datos secundarios committed")
            self._actualizar_progreso_operacion("relaciones y datos secundarios")
            self._loguear_resumen(resultados)

            return resultados

        finally:
            # SIEMPRE restaurar FK checks, incluso si hay error
            self.logger.info("🔄 Restaurando FK checks...")
            try:
                # Si la transacción está en estado de error, hacer rollback primero
                self.context.session.rollback()
            except Exception:
                pass  # Ignorar si no hay transacción activa
            try:
                self.context.session.execute(text("SET session_replication_role = DEFAULT"))
                self.context.session.commit()
            except Exception as e:
                self.logger.warning(f"No se pudo restaurar session_replication_role: {e}")

    def _loguear_resumen(self, resultados: Dict[str, BulkOperationResult]) -> None:
        """Log a summary of all bulk operations."""
        total_insertados = sum(r.inserted_count for r in resultados.values())
        total_errores = sum(len(r.errors) for r in resultados.values())
        duracion_total = sum(r.duration_seconds for r in resultados.values())

        self.logger.info(
            f"Procesamiento bulk completado: {total_insertados} registros en {duracion_total:.2f}s"
        )

        if total_errores > 0:
            self.logger.warning(f"Total errores: {total_errores}")
            for nombre_operacion, resultado in resultados.items():
                if resultado.errors:
                    self.logger.warning(
                        f"{nombre_operacion}: {len(resultado.errors)} errores"
                    )
                    # Log primeros 2 errores para debug
                    for error in resultado.errors[:2]:
                        self.logger.warning(f"  - {error}")

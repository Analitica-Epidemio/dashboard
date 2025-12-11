"""
Procesador para CLI_P26 (Casos Clínicos Ambulatorios).

Guarda en: ConteoCasosClinicos
"""

import logging

import polars as pl

from app.domains.vigilancia_agregada.constants import OrigenDatosPasivos
from app.domains.vigilancia_agregada.models.cargas import NotificacionSemanal
from app.domains.vigilancia_agregada.models.catalogos import (
    RangoEtario,
    TipoCasoEpidemiologicoPasivo,
)
from app.domains.vigilancia_agregada.models.conteos import ConteoCasosClinicos

from ..columns.base import ColumnRegistry
from ..columns.cli_p26 import CLI_P26_COLUMNS
from .base_type import FileTypeProcessor, ProcessingResult

logger = logging.getLogger(__name__)


class CLIP26Processor(FileTypeProcessor):
    """
    Procesador para archivos CLI_P26 (Casos Clínicos Ambulatorios).

    Transforma datos del Excel a ConteoCasosClinicos agrupando por:
    - NotificacionSemanal (anio, semana, establecimiento)
    - TipoCasoEpidemiologicoPasivo (evento)
    - RangoEtario (grupo de edad)
    - Sexo
    """

    @property
    def file_type(self) -> str:
        return "CLI_P26"

    @property
    def column_registry(self) -> ColumnRegistry:
        return CLI_P26_COLUMNS

    def transform(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Transforma el DataFrame CLI_P26 a formato interno.
        """
        # Renombrar columnas
        df = self.column_registry.rename_columns(df)

        # Filtrar registros vacíos / de control
        # Validación: Filas con "CARGADA DATOS CERO" no contienen casos y duplican IDs (generalmente 0).
        if "estado" in df.columns:
            df = df.filter(pl.col("estado") != "CARGADA DATOS CERO")

        # Normalizar sexo
        df = df.with_columns(
            pl.col("sexo")
            .str.to_uppercase()
            .str.strip_chars()
            .replace({"MASCULINO": "M", "FEMENINO": "F", "": "X"})
            .fill_null("X")
            .alias("sexo")
        )

        # Asegurar tipos numéricos
        df = df.with_columns(
            [
                pl.col("id_agrp_clinica").cast(pl.Int64),
                pl.col("anio").cast(pl.Int32),
                pl.col("semana").cast(pl.Int32),
                pl.col("id_origen").cast(pl.Int64),
                pl.col("id_snvs_evento").cast(pl.Int64),
                pl.col("id_edad").cast(pl.Int32),
                pl.col("cantidad").cast(pl.Int32),
            ]
        )

        # Filtrar registros con cantidad > 0 y estado válido
        df = df.filter(
            (pl.col("cantidad") > 0) | (pl.col("estado") != "CARGADA DATOS CERO")
        )

        return df

    def save_to_db(self, df: pl.DataFrame) -> ProcessingResult:
        """
        Guarda los datos en la base de datos.

        Proceso:
        1. Crear establecimientos que no existen
        2. Agrupar por (id_encabezado, anio, semana, id_origen) → NotificacionSemanal
        3. Lookup/crear catálogos
        4. Bulk insert ConteoCasosClinicos
        """
        try:
            total_rows = len(df)
            inserted = 0
            updated = 0
            errors = []

            # Paso 1: Asegurar que existen los establecimientos
            self._update_progress(30, "Verificando establecimientos")
            self._ensure_establecimientos_exist(df)

            # Agrupar datos por notificación
            groups = df.group_by(
                ["id_encabezado", "anio", "semana", "id_origen", "nombre_origen"]
            ).agg([pl.len().alias("n_registros")])

            self._update_progress(40, f"Procesando {len(groups)} notificaciones")

            # Cache de catálogos
            eventos_cache: dict[int, int] = {}
            edades_cache: dict[int, int] = {}
            notificaciones_cache: dict[tuple, int] = {}

            # Precargar catálogos existentes
            self._preload_catalogos(eventos_cache, edades_cache)

            # Procesar cada notificación
            for i, notif_row in enumerate(groups.iter_rows(named=True)):
                id_encabezado = notif_row["id_encabezado"]
                anio = notif_row["anio"]
                semana = notif_row["semana"]
                id_origen = notif_row["id_origen"]
                nombre_origen = notif_row["nombre_origen"]

                # Obtener o crear NotificacionSemanal
                notif_id = self._get_or_create_notificacion(
                    id_encabezado,
                    anio,
                    semana,
                    id_origen,
                    nombre_origen,
                    notificaciones_cache,
                )

                # Obtener filas de esta notificación
                notif_df = df.filter(pl.col("id_encabezado") == id_encabezado)

                # Procesar cada conteo
                for row in notif_df.iter_rows(named=True):
                    try:
                        evento_id = self._get_or_create_evento(
                            row["id_snvs_evento"], row["nombre_evento"], eventos_cache
                        )
                        edad_id = self._get_or_create_edad(
                            row["id_edad"], row["nombre_grupo_etario"], edades_cache
                        )

                        conteo = ConteoCasosClinicos(
                            id_snvs=row["id_agrp_clinica"],
                            notificacion_id=notif_id,
                            tipo_evento_id=evento_id,
                            rango_etario_id=edad_id,
                            sexo=row.get("sexo"),
                            cantidad=row["cantidad"],
                        )
                        self.session.add(conteo)
                        inserted += 1

                    except Exception as e:
                        errors.append(f"Error en fila: {str(e)}")

                # Commit cada 100 notificaciones
                if i % 100 == 0:
                    self.session.commit()
                    self._update_progress(
                        40 + int((i / len(groups)) * 55),
                        f"Procesadas {i}/{len(groups)} notificaciones",
                    )

            # Commit final
            self.session.commit()

            return ProcessingResult(
                status="SUCCESS" if not errors else "PARTIAL",
                total_rows=total_rows,
                processed_rows=inserted + updated,
                inserted_count=inserted,
                updated_count=updated,
                errors=errors[:10],  # Limitar errores reportados
            )

        except Exception as e:
            logger.error(f"Error guardando CLI_P26: {e}", exc_info=True)
            self.session.rollback()
            return ProcessingResult(
                status="FAILED",
                total_rows=len(df),
                processed_rows=0,
                inserted_count=0,
                updated_count=0,
                errors=[str(e)],
            )

    def _preload_catalogos(
        self,
        eventos_cache: dict[int, int],
        edades_cache: dict[int, int],
    ) -> None:
        """Precarga catálogos existentes en cache."""
        # Eventos
        from sqlmodel import select

        eventos = self.session.exec(
            select(
                TipoCasoEpidemiologicoPasivo.id_snvs, TipoCasoEpidemiologicoPasivo.id
            )
        ).all()
        for id_snvs, id_interno in eventos:
            if id_snvs:
                eventos_cache[id_snvs] = id_interno

        # Edades
        edades = self.session.exec(select(RangoEtario.id_snvs, RangoEtario.id)).all()
        for id_snvs, id_interno in edades:
            if id_snvs:
                edades_cache[id_snvs] = id_interno

    def _get_or_create_notificacion(
        self,
        id_encabezado: int,
        anio: int,
        semana: int,
        id_origen: int,
        nombre_origen: str,
        cache: dict[tuple, int],
    ) -> int:
        """Obtiene o crea NotificacionSemanal."""
        # Primero obtener el ID interno del establecimiento por su codigo_snvs
        from sqlmodel import select

        from app.domains.territorio.establecimientos_models import Establecimiento

        estab_stmt = select(Establecimiento.id).where(
            Establecimiento.codigo_snvs == str(id_origen)
        )
        estab_result = self.session.exec(estab_stmt).first()
        establecimiento_id_interno = estab_result if estab_result else None

        if not establecimiento_id_interno:
            logger.warning(f"Establecimiento con codigo_snvs={id_origen} no encontrado")
            # Crear uno de emergencia
            estab = Establecimiento(
                codigo_snvs=str(id_origen),
                nombre=nombre_origen or f"Establecimiento SNVS {id_origen}",
                source="SNVS",
            )
            self.session.add(estab)
            self.session.flush()
            establecimiento_id_interno = estab.id

        key = (anio, semana, establecimiento_id_interno)

        if key in cache:
            return cache[key]

        # Buscar notificación existente
        if id_encabezado:
            stmt = select(NotificacionSemanal).where(
                NotificacionSemanal.id_snvs == id_encabezado
            )
            existing = self.session.exec(stmt).first()
            if existing:
                cache[key] = existing.id  # type: ignore[assignment]
                return existing.id  # type: ignore[return-value]

        stmt = select(NotificacionSemanal).where(
            NotificacionSemanal.anio == anio,
            NotificacionSemanal.semana == semana,
            NotificacionSemanal.establecimiento_id == establecimiento_id_interno,
        )
        existing = self.session.exec(stmt).first()

        if existing:
            cache[key] = existing.id  # type: ignore[assignment]
            return existing.id  # type: ignore[return-value]

        # Crear nueva
        notif = NotificacionSemanal(
            id_snvs=id_encabezado,
            anio=anio,
            semana=semana,
            origen=OrigenDatosPasivos.CLINICO,
            establecimiento_id=establecimiento_id_interno,
        )
        self.session.add(notif)
        self.session.flush()
        cache[key] = notif.id  # type: ignore[assignment]
        return notif.id  # type: ignore[return-value]

    def _get_or_create_evento(
        self,
        id_snvs: int,
        nombre: str,
        cache: dict[int, int],
    ) -> int:
        """Obtiene o crea TipoCasoEpidemiologicoPasivo."""
        if id_snvs in cache:
            return cache[id_snvs]

        from sqlmodel import select

        stmt = select(TipoCasoEpidemiologicoPasivo).where(
            TipoCasoEpidemiologicoPasivo.id_snvs == id_snvs
        )
        existing = self.session.exec(stmt).first()

        if existing:
            cache[id_snvs] = existing.id  # type: ignore[assignment]
            return existing.id  # type: ignore[return-value]

        # Generar slug kebab-case desde el nombre
        slug = self._generate_slug(nombre, id_snvs)

        evento = TipoCasoEpidemiologicoPasivo(
            slug=slug,
            id_snvs=id_snvs,
            nombre=nombre,
            origen=OrigenDatosPasivos.CLINICO,
        )
        self.session.add(evento)
        self.session.flush()
        cache[id_snvs] = evento.id  # type: ignore[assignment]
        return evento.id  # type: ignore[return-value]

    def _generate_slug(self, nombre: str, id_snvs: int) -> str:
        """
        Genera un slug kebab-case único desde el nombre del evento.

        Ejemplos:
        - "ETI" -> "eti"
        - "Neumonía" -> "neumonia"
        - "Bronquiolitis" -> "bronquiolitis"
        - "Diarreas agudas" -> "diarreas-agudas"
        """
        import re
        import unicodedata

        # Normalizar: remover acentos
        normalized = unicodedata.normalize("NFKD", nombre)
        ascii_text = normalized.encode("ascii", "ignore").decode("ascii")

        # Convertir a minúsculas y reemplazar espacios/caracteres especiales
        slug = ascii_text.lower()
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        slug = slug.strip("-")

        # Si el slug queda vacío, usar id_snvs como fallback
        if not slug:
            slug = f"evento-{id_snvs}"

        return slug

    def _get_or_create_edad(
        self,
        id_snvs: int,
        nombre: str,
        cache: dict[int, int],
    ) -> int:
        """Obtiene o crea RangoEtario."""
        if id_snvs in cache:
            return cache[id_snvs]

        from sqlmodel import select

        stmt = select(RangoEtario).where(RangoEtario.id_snvs == id_snvs)
        existing = self.session.exec(stmt).first()

        if existing:
            cache[id_snvs] = existing.id  # type: ignore[assignment]
            return existing.id  # type: ignore[return-value]

        edad = RangoEtario(
            id_snvs=id_snvs,
            nombre=nombre,
            orden=id_snvs,  # Usar id_snvs como orden por defecto
            origen=OrigenDatosPasivos.CLINICO,
        )
        self.session.add(edad)
        self.session.flush()
        cache[id_snvs] = edad.id  # type: ignore[assignment]
        return edad.id  # type: ignore[return-value]

    def _ensure_establecimientos_exist(self, df: pl.DataFrame) -> None:
        """
        Asegura que todos los establecimientos referenciados existen en la BD.

        Crea establecimientos faltantes con source='SNVS'.
        Similar a como hace el procesador de nominales.
        """
        from datetime import datetime, timezone

        from sqlalchemy import inspect
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        from app.domains.territorio.establecimientos_models import Establecimiento

        # Extraer establecimientos únicos del DataFrame
        estab_df = df.select(
            [
                pl.col("id_origen").cast(pl.Int64).alias("id_snvs"),
                pl.col("nombre_origen")
                .str.strip_chars()
                .str.to_uppercase()
                .alias("nombre"),
            ]
        ).unique()

        ids_snvs = [
            str(row["id_snvs"])
            for row in estab_df.iter_rows(named=True)
            if row["id_snvs"]
        ]

        if not ids_snvs:
            return

        # Buscar cuáles ya existen por codigo_snvs
        from sqlmodel import col, select

        stmt = select(Establecimiento.codigo_snvs).where(
            col(Establecimiento.codigo_snvs).in_(ids_snvs)
        )
        existentes = {r[0] for r in self.session.execute(stmt).all() if r[0]}

        # Crear los que faltan
        faltantes = [
            row
            for row in estab_df.iter_rows(named=True)
            if row["id_snvs"] and str(row["id_snvs"]) not in existentes
        ]

        if faltantes:
            logger.info(f"➕ Creando {len(faltantes)} establecimientos faltantes")
            timestamp = datetime.now(timezone.utc)
            nuevos = [
                {
                    "codigo_snvs": str(row["id_snvs"]),
                    "nombre": row["nombre"] or f"Establecimiento SNVS {row['id_snvs']}",
                    "source": "SNVS",
                    "created_at": timestamp,
                    "updated_at": timestamp,
                }
                for row in faltantes
            ]

            stmt = pg_insert(inspect(Establecimiento).local_table).values(nuevos)
            self.session.execute(stmt.on_conflict_do_nothing())
            self.session.flush()
            logger.info("✅ Establecimientos creados")

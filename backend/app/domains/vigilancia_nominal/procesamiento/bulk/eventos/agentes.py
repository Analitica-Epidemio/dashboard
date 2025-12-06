"""
Processor determinista para extraccion de agentes desde CSV.

MATCH EXACTO - No usa regex ni "contains".
Cada regla especifica el valor EXACTO del campo que debe matchear.

Basado en analisis del CSV real de CHUBUT.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import polars as pl
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domains.catalogos.agentes.models import AgenteEtiologico
from app.domains.vigilancia_nominal.models.agentes import (
    CasoAgente,
    ResultadoDeteccion,
)

from ..shared import BulkOperationResult, get_current_timestamp

# =============================================================================
# REGLAS DE EXTRACCION - MATCH EXACTO
# =============================================================================
# Estructura:
#   EVENTO (nombre exacto) -> lista de reglas
#   Cada regla:
#     - campo: columna CSV
#     - valor: valor EXACTO que debe tener (case-insensitive)
#     - agente_codigo: codigo en tabla agente_etiologico
#     - campo_resultado: (opcional) columna para verificar +/-
#     - valores_positivos: (opcional) valores exactos que indican positivo
#     - metodo: metodo de deteccion
# =============================================================================

REGLAS_EXTRACCION: Dict[str, List[Dict[str, Any]]] = {
    # =========================================================================
    # UC-IRAG - Unidad Centinela de Infeccion Respiratoria Aguda Grave
    # =========================================================================
    "Unidad Centinela de Infección Respiratoria Aguda Grave (UC-IRAG)": [
        # VSR
        {
            "campo": "DETERMINACION",
            "valor": "Antígeno viral de VSR",
            "agente_codigo": "vsr",
            "campo_resultado": "RESULTADO",
            "valores_positivos": ["Positivo", "Detectable"],
            "metodo": "antigeno",
        },
        # Influenza A
        {
            "campo": "DETERMINACION",
            "valor": "Antígeno viral de influenza A",
            "agente_codigo": "influenza-a",
            "campo_resultado": "RESULTADO",
            "valores_positivos": ["Positivo", "Detectable"],
            "metodo": "antigeno",
        },
        {
            "campo": "DETERMINACION",
            "valor": "Genoma viral de Influenza A (sin subtipificar)",
            "agente_codigo": "influenza-a",
            "campo_resultado": "RESULTADO",
            "valores_positivos": ["Positivo", "Detectable"],
            "metodo": "PCR",
        },
        # Influenza B
        {
            "campo": "DETERMINACION",
            "valor": "Antígeno viral de influenza B",
            "agente_codigo": "influenza-b",
            "campo_resultado": "RESULTADO",
            "valores_positivos": ["Positivo", "Detectable"],
            "metodo": "antigeno",
        },
        # SARS-CoV-2
        {
            "campo": "DETERMINACION",
            "valor": "Genoma viral SARS-CoV-2",
            "agente_codigo": "sars-cov-2",
            "campo_resultado": "RESULTADO",
            "valores_positivos": ["Positivo", "Detectable"],
            "metodo": "PCR",
        },
        {
            "campo": "DETERMINACION",
            "valor": "Detección de genoma viral SARs COV-2, Influenza y VSR (negativo)",
            "agente_codigo": "sars-cov-2",
            "campo_resultado": "RESULTADO",
            "valores_positivos": ["Positivo", "Detectable"],
            "metodo": "PCR",
        },
        # Adenovirus
        {
            "campo": "DETERMINACION",
            "valor": "Antígeno viral de ADV",
            "agente_codigo": "adenovirus",
            "campo_resultado": "RESULTADO",
            "valores_positivos": ["Positivo", "Detectable"],
            "metodo": "antigeno",
        },
        # Metapneumovirus
        {
            "campo": "DETERMINACION",
            "valor": "Antigeno viral Metaneumovirus Humano",
            "agente_codigo": "metapneumovirus",
            "campo_resultado": "RESULTADO",
            "valores_positivos": ["Positivo", "Detectable"],
            "metodo": "antigeno",
        },
        {
            "campo": "DETERMINACION",
            "valor": "Genoma viral de Metaneumovirus Humano",
            "agente_codigo": "metapneumovirus",
            "campo_resultado": "RESULTADO",
            "valores_positivos": ["Positivo", "Detectable"],
            "metodo": "PCR",
        },
        # Parainfluenza 1
        {
            "campo": "DETERMINACION",
            "valor": "Antígeno viral de  Parainfluenza 1",
            "agente_codigo": "parainfluenza-1",
            "campo_resultado": "RESULTADO",
            "valores_positivos": ["Positivo", "Detectable"],
            "metodo": "antigeno",
        },
        # Parainfluenza 2
        {
            "campo": "DETERMINACION",
            "valor": "Antígeno viral de  Parainfluenza 2",
            "agente_codigo": "parainfluenza-2",
            "campo_resultado": "RESULTADO",
            "valores_positivos": ["Positivo", "Detectable"],
            "metodo": "antigeno",
        },
        # Parainfluenza 3
        {
            "campo": "DETERMINACION",
            "valor": "Antígeno viral de  Parainfluenza 3",
            "agente_codigo": "parainfluenza-3",
            "campo_resultado": "RESULTADO",
            "valores_positivos": ["Positivo", "Detectable"],
            "metodo": "antigeno",
        },
    ],

    # =========================================================================
    # Diarrea aguda
    # =========================================================================
    "Diarrea aguda": [
        # STEC O157 - por CLASIFICACION_MANUAL
        {
            "campo": "CLASIFICACION_MANUAL",
            "valor": "Diarrea aguda por STEC O157",
            "agente_codigo": "stec-o157",
            "metodo": "clasificacion",
        },
        {
            "campo": "CLASIFICACION_MANUAL",
            "valor": "Diarrea aguda sanguinolenta por STEC O157",
            "agente_codigo": "stec-o157",
            "metodo": "clasificacion",
        },
        # Rotavirus - por DETERMINACION
        {
            "campo": "DETERMINACION",
            "valor": "Antígeno viral de Rotavirus",
            "agente_codigo": "rotavirus",
            "campo_resultado": "RESULTADO",
            "valores_positivos": ["Positivo", "Detectable"],
            "metodo": "antigeno",
        },
        # Adenovirus enterico - por DETERMINACION
        {
            "campo": "DETERMINACION",
            "valor": "Antígeno viral de Adenovirus",
            "agente_codigo": "adenovirus-enterico",
            "campo_resultado": "RESULTADO",
            "valores_positivos": ["Positivo", "Detectable"],
            "metodo": "antigeno",
        },
        # Rotavirus/Adenovirus mixto - por CLASIFICACION_MANUAL
        {
            "campo": "CLASIFICACION_MANUAL",
            "valor": "Diarreas aguda por infección mixta Rotavirus/Adenovirus 40-41",
            "agente_codigo": "rotavirus",
            "metodo": "clasificacion",
        },
    ],

    # =========================================================================
    # SUH - Sindrome Uremico Hemolitico
    # =========================================================================
    "SUH - Sindrome Urémico Hemolítico": [
        # STEC O157
        {
            "campo": "CLASIFICACION_MANUAL",
            "valor": "Caso de SUH con criterio de infección por STEC O157",
            "agente_codigo": "stec-o157",
            "metodo": "clasificacion",
        },
        # STEC no-O157
        {
            "campo": "CLASIFICACION_MANUAL",
            "valor": "Caso de SUH con criterio de infección por STEC no-O157",
            "agente_codigo": "stec-no-o157",
            "metodo": "clasificacion",
        },
    ],

    # =========================================================================
    # Dengue
    # =========================================================================
    "Dengue": [
        # DEN-1
        {
            "campo": "CLASIFICACION_MANUAL",
            "valor": "Caso confirmado DEN-1",
            "agente_codigo": "dengue-1",
            "metodo": "clasificacion",
        },
        # DEN-2
        {
            "campo": "CLASIFICACION_MANUAL",
            "valor": "Caso confirmado DEN-2",
            "agente_codigo": "dengue-2",
            "metodo": "clasificacion",
        },
        # Sin serotipo
        {
            "campo": "CLASIFICACION_MANUAL",
            "valor": "Caso confirmado sin serotipo",
            "agente_codigo": "dengue-sin-serotipo",
            "metodo": "clasificacion",
        },
        # NS1 antigen
        {
            "campo": "DETERMINACION",
            "valor": "Antígeno NS1",
            "agente_codigo": "dengue-sin-serotipo",
            "campo_resultado": "RESULTADO",
            "valores_positivos": ["Positivo", "Detectable", "Reactivo"],
            "metodo": "NS1",
        },
        # IgM
        {
            "campo": "DETERMINACION",
            "valor": "IgM DENV",
            "agente_codigo": "dengue-sin-serotipo",
            "campo_resultado": "RESULTADO",
            "valores_positivos": ["Positivo", "Detectable", "Reactivo"],
            "metodo": "serologia",
        },
        # Genoma viral
        {
            "campo": "DETERMINACION",
            "valor": "Genoma viral",
            "agente_codigo": "dengue-sin-serotipo",
            "campo_resultado": "RESULTADO",
            "valores_positivos": ["Positivo", "Detectable"],
            "metodo": "PCR",
        },
    ],

    # =========================================================================
    # Meningoencefalitis
    # =========================================================================
    "Meningoencefalitis": [
        # Streptococcus pneumoniae
        {
            "campo": "CLASIFICACION_MANUAL",
            "valor": "Caso confirmado de meningoencefalitis por Streptococcus pneumoniae",
            "agente_codigo": "streptococcus-pneumoniae",
            "metodo": "clasificacion",
        },
        # Herpes simple
        {
            "campo": "CLASIFICACION_MANUAL",
            "valor": "Caso confirmado de Encefalitis por herpes simple",
            "agente_codigo": "herpes-simple",
            "metodo": "clasificacion",
        },
    ],

    # =========================================================================
    # Otras infecciones invasivas
    # =========================================================================
    "Otras infecciones invasivas (bacterianas y otras)": [
        # Streptococcus pyogenes
        {
            "campo": "CLASIFICACION_MANUAL",
            "valor": "Caso confirmado de Streptococco pyogenes",
            "agente_codigo": "streptococcus-pyogenes",
            "metodo": "clasificacion",
        },
        {
            "campo": "CLASIFICACION_MANUAL",
            "valor": "S.pyogenes M1 linaje global",
            "agente_codigo": "streptococcus-pyogenes",
            "metodo": "clasificacion",
        },
        # Streptococcus pneumoniae
        {
            "campo": "CLASIFICACION_MANUAL",
            "valor": "Caso confirmado de Streptococcus pneumoniae",
            "agente_codigo": "streptococcus-pneumoniae",
            "metodo": "clasificacion",
        },
    ],
}

# Valores EXACTOS que indican resultado NEGATIVO
VALORES_NEGATIVOS = [
    "Negativo",
    "No detectable",
    "No detectado",
    "No reactivo",
]


class AgentesExtractor:
    """
    Extrae agentes de eventos usando MATCH EXACTO.

    NO usa regex ni "contains". Solo igualdad exacta (case-insensitive).
    """

    def __init__(self, context, logger: logging.Logger):
        self.context = context
        self.logger = logger
        self._agentes_by_codigo: Optional[Dict[str, int]] = None
        # Pre-computar mapping case-insensitive de reglas
        self._reglas_lower: Dict[str, List[Dict[str, Any]]] = {
            k.lower(): v for k, v in REGLAS_EXTRACCION.items()
        }

    def _load_agentes_by_codigo(self) -> Dict[str, int]:
        """Carga mapping codigo -> id de agentes activos."""
        if self._agentes_by_codigo is not None:
            return self._agentes_by_codigo

        stmt = select(AgenteEtiologico.id, AgenteEtiologico.slug).where(
            AgenteEtiologico.activo == True  # noqa: E712
        )
        result = self.context.session.execute(stmt)
        rows = result.fetchall()

        self._agentes_by_codigo = {row.slug: row.id for row in rows}  # Cambiado de codigo a slug
        return self._agentes_by_codigo

    def _match_exacto(self, valor_csv: Any, valor_regla: str) -> bool:
        """
        Compara dos valores con IGUALDAD EXACTA (case-insensitive).

        Args:
            valor_csv: Valor del CSV (puede ser None o cualquier tipo)
            valor_regla: Valor esperado de la regla

        Returns:
            True solo si son exactamente iguales (ignorando case)
        """
        if valor_csv is None:
            return False

        valor_str = str(valor_csv).strip()
        return valor_str.lower() == valor_regla.lower()

    def _determinar_resultado(
        self,
        row: Dict[str, Any],
        regla: Dict[str, Any],
    ) -> Tuple[ResultadoDeteccion, Optional[str]]:
        """
        Determina si el resultado es positivo/negativo/indeterminado.

        Si no hay campo_resultado en la regla, asume POSITIVO
        (la clasificacion manual ya indica el agente confirmado).
        """
        campo_resultado = regla.get("campo_resultado")

        # Sin campo de resultado = positivo por clasificacion
        if not campo_resultado:
            return ResultadoDeteccion.POSITIVO, None

        valor_raw = row.get(campo_resultado)
        if valor_raw is None:
            return ResultadoDeteccion.INDETERMINADO, None

        valor_str = str(valor_raw).strip()

        # Verificar positivos (match exacto)
        valores_positivos = regla.get("valores_positivos", [])
        for vp in valores_positivos:
            if valor_str.lower() == vp.lower():
                return ResultadoDeteccion.POSITIVO, valor_str

        # Verificar negativos (match exacto)
        for neg in VALORES_NEGATIVOS:
            if valor_str.lower() == neg.lower():
                return ResultadoDeteccion.NEGATIVO, valor_str

        return ResultadoDeteccion.INDETERMINADO, valor_str

    def _extraer_agentes_de_fila(
        self,
        row: Dict[str, Any],
        id_evento: int,
        evento_nombre: str,
        agentes_by_codigo: Dict[str, int],
    ) -> List[Dict[str, Any]]:
        """
        Extrae agentes de una fila usando las reglas del evento.

        Returns:
            Lista de dicts listos para insertar en evento_agente
        """
        agentes_encontrados: List[Dict[str, Any]] = []
        agentes_ya_agregados: Set[str] = set()

        # Obtener reglas (case-insensitive, O(1) lookup)
        evento_lower = evento_nombre.lower() if evento_nombre else ""
        reglas = self._reglas_lower.get(evento_lower)
        if not reglas:
            return agentes_encontrados

        for regla in reglas:
            campo = regla["campo"]
            valor_esperado = regla["valor"]
            agente_codigo = regla["agente_codigo"]

            # Verificar que el agente existe en BD
            id_agente = agentes_by_codigo.get(agente_codigo)
            if not id_agente:
                continue

            # Evitar duplicados del mismo agente
            if agente_codigo in agentes_ya_agregados:
                continue

            # Obtener valor del campo
            valor_campo = row.get(campo)

            # MATCH EXACTO
            if not self._match_exacto(valor_campo, valor_esperado):
                continue

            # Determinar resultado
            resultado, resultado_raw = self._determinar_resultado(row, regla)

            agente_data = {
                "id_caso": id_evento,
                "id_agente": id_agente,
                "resultado": resultado.value,
                "metodo_deteccion": regla.get("metodo"),
                "resultado_raw": resultado_raw,
                "fecha_deteccion": None,
                "id_config_usada": None,
                "campo_origen": campo,
                "valor_origen": str(valor_campo)[:500] if valor_campo else None,
                "created_at": get_current_timestamp(),
                "updated_at": get_current_timestamp(),
            }

            agentes_encontrados.append(agente_data)
            agentes_ya_agregados.add(agente_codigo)

        return agentes_encontrados

    def _load_tipo_eno_mapping(self) -> Dict[str, int]:
        """No usado - mantenido por compatibilidad."""
        return {}

    def upsert_agentes_eventos(
        self,
        df: pl.DataFrame,
        evento_mapping: Dict[int, int],
    ) -> BulkOperationResult:
        """
        Extrae y guarda agentes de los eventos del CSV.

        Usa MATCH EXACTO con valores del CSV.
        """
        start_time = datetime.now()
        errors: List[str] = []
        inserted_count = 0

        self.logger.info("📊 Extrayendo agentes etiológicos...")

        # Verificar columnas requeridas
        required_cols = ["IDEVENTOCASO", "EVENTO"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            return BulkOperationResult(
                inserted_count=0,
                errors=[f"Columnas faltantes: {missing}"],
                duration_seconds=(datetime.now() - start_time).total_seconds(),
            )

        # Cargar agentes de BD
        agentes_by_codigo = self._load_agentes_by_codigo()
        if not agentes_by_codigo:
            self.logger.warning("  No hay agentes en la BD")
            return BulkOperationResult(
                inserted_count=0,
                errors=["No hay agentes configurados en la BD"],
                duration_seconds=(datetime.now() - start_time).total_seconds(),
            )

        # DEBUG: Ver qué eventos hay en el CSV vs reglas
        eventos_csv = set(df["EVENTO"].drop_nulls().unique().to_list())
        eventos_csv_lower = {e.lower(): e for e in eventos_csv}
        eventos_con_match = set(eventos_csv_lower.keys()).intersection(self._reglas_lower.keys())

        self.logger.info(f"  CasoEpidemiologicos CSV: {len(eventos_csv)}, reglas: {len(self._reglas_lower)}, match: {len(eventos_con_match)}")
        if eventos_con_match:
            matched_names = [eventos_csv_lower[e] for e in list(eventos_con_match)[:5]]
            self.logger.info(f"  ✓ Con reglas: {matched_names}")

        # Procesar filas
        all_agentes_data: List[Dict[str, Any]] = []
        filas_procesadas = 0
        filas_con_agentes = 0

        df_dicts = df.to_dicts()

        for row in df_dicts:
            id_evento_caso = row.get("IDEVENTOCASO")
            evento_nombre = row.get("EVENTO")

            if not id_evento_caso or not evento_nombre:
                continue

            # Convertir IDEVENTOCASO a int
            try:
                id_evento_caso_int = int(float(id_evento_caso))
            except (ValueError, TypeError):
                continue

            # Obtener id_evento de la BD
            id_evento = evento_mapping.get(id_evento_caso_int)
            if not id_evento:
                continue

            filas_procesadas += 1

            # Extraer agentes
            agentes = self._extraer_agentes_de_fila(
                row, id_evento, evento_nombre, agentes_by_codigo
            )

            if agentes:
                all_agentes_data.extend(agentes)
                filas_con_agentes += 1

        self.logger.debug(
            f"  Filas={filas_procesadas}, con agentes={filas_con_agentes}, detecciones={len(all_agentes_data)}"
        )

        if not all_agentes_data:
            return BulkOperationResult(
                inserted_count=0,
                updated_count=0,
                skipped_count=0,
                errors=[],
                duration_seconds=(datetime.now() - start_time).total_seconds(),
            )

        # Deduplicar (mismo evento + mismo agente)
        seen: Set[Tuple[int, int]] = set()
        unique_agentes: List[Dict[str, Any]] = []
        for a in all_agentes_data:
            key = (a["id_caso"], a["id_agente"])
            if key not in seen:
                seen.add(key)
                unique_agentes.append(a)

        self.logger.debug(f"  {len(unique_agentes)} registros únicos tras dedup")

        # Bulk insert/update
        try:
            stmt = pg_insert(CasoAgente.__table__).values(unique_agentes)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_caso_agente",  # Cambiado de uq_evento_agente a uq_caso_agente
                set_={
                    "resultado": stmt.excluded.resultado,
                    "metodo_deteccion": stmt.excluded.metodo_deteccion,
                    "resultado_raw": stmt.excluded.resultado_raw,
                    "campo_origen": stmt.excluded.campo_origen,
                    "valor_origen": stmt.excluded.valor_origen,
                    "updated_at": stmt.excluded.updated_at,
                },
            )
            self.context.session.execute(stmt)
            inserted_count = len(unique_agentes)

        except Exception as e:
            errors.append(f"Error en bulk insert: {str(e)}")
            self.logger.error(f"  Error: {e}")

        duration = (datetime.now() - start_time).total_seconds()
        return BulkOperationResult(
            inserted_count=inserted_count,
            updated_count=0,
            skipped_count=0,
            errors=errors,
            duration_seconds=duration,
        )

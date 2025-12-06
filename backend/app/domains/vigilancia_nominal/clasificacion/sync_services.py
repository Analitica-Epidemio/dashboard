"""
Servicios síncronos para clasificación de eventos usando estrategias de DB.
"""

from typing import Any, Dict, List, Optional

import pandas as pd
from sqlmodel import Session, col, select

from app.domains.vigilancia_nominal.clasificacion.models import (
    ClassificationRule,
    EstrategiaClasificacion,
    FilterCondition,
    TipoClasificacion,
    TipoFiltro,
)


class SyncEventClassificationService:
    """
    Servicio síncrono para clasificar eventos usando estrategias de DB.

    Versión síncrona del EventClassificationService para usar en Celery.
    """

    def __init__(self, session: Session):
        """
        Inicializa el servicio de clasificación síncrono.

        Args:
            session: Sesión de base de datos síncrona
        """
        self.session = session
        self._cache: Dict[int, EstrategiaClasificacion] = {}

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normaliza texto para comparación insensible.
        - Convierte a minúsculas
        - Elimina acentos
        - Elimina espacios múltiples
        - Trim espacios al inicio y final
        """
        import unicodedata

        if not text or not isinstance(text, str):
            return ""

        # Convertir a minúsculas
        text = text.lower().strip()

        # Eliminar acentos
        text = "".join(
            c
            for c in unicodedata.normalize("NFD", text)
            if unicodedata.category(c) != "Mn"
        )

        # Reemplazar múltiples espacios por uno solo
        text = " ".join(text.split())

        return text

    def classify_events(
        self, df: pd.DataFrame, id_enfermedad: int, use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Clasifica eventos según la estrategia definida para un tipo de ENO.

        Args:
            df: DataFrame con los eventos a clasificar
            id_enfermedad: ID del tipo de ENO
            use_cache: Si usar cache de estrategias

        Returns:
            DataFrame con columnas 'clasificacion', 'es_positivo', 'id_estrategia_aplicada' y 'trazabilidad' agregadas
        """
        # Obtener estrategia
        strategy = self._get_strategy(id_enfermedad, use_cache)

        # Inicializar columnas de trazabilidad
        df["clasificacion"] = None
        df["es_positivo"] = False
        df["id_estrategia_aplicada"] = None
        df["trazabilidad"] = None

        if not strategy:
            # Sin estrategia definida, marcar como sin clasificar
            df["clasificacion"] = TipoClasificacion.REQUIERE_REVISION.value
            df["trazabilidad"] = df.apply(
                lambda row: {
                    "razon": "sin_estrategia",
                    "mensaje": f"No existe estrategia definida para id_enfermedad={id_enfermedad}",
                    "estrategia_evaluada": False,
                },
                axis=1,
            )
            return df

        # Guardar ID de estrategia aplicada
        df["id_estrategia_aplicada"] = strategy.id

        # Aplicar configuración específica de la estrategia
        df = self._apply_strategy_config(df, strategy)

        # Obtener reglas ordenadas por prioridad
        rules = sorted(
            [r for r in strategy.classification_rules if r.is_active],
            key=lambda r: r.priority,
        )

        # Aplicar cada regla y capturar trazabilidad
        for rule in rules:
            # Solo aplicar a filas aún no clasificadas
            unclassified_mask = df["clasificacion"].isna()
            if not unclassified_mask.any():
                break

            # Evaluar condiciones de la regla con trazabilidad
            rule_mask, traceability = self._apply_rule_with_traceability(
                df[unclassified_mask].copy(), rule
            )

            # Aplicar clasificación donde se cumple la regla
            indices = df[unclassified_mask][rule_mask].index

            if len(indices) > 0:
                df.loc[indices, "clasificacion"] = rule.classification

                # Marcar como positivo si corresponde
                if rule.classification in [
                    TipoClasificacion.CONFIRMADOS.value,
                    TipoClasificacion.CON_RESULTADO_MORTAL.value,
                ]:
                    df.loc[indices, "es_positivo"] = True

                # Guardar trazabilidad para filas clasificadas
                for idx in indices:
                    df.at[idx, "trazabilidad"] = {
                        "razon": "regla_aplicada",
                        "estrategia_id": strategy.id,
                        "estrategia_nombre": strategy.name,
                        "regla_id": rule.id,
                        "regla_nombre": rule.name,
                        "regla_prioridad": rule.priority,
                        "clasificacion_aplicada": rule.classification,
                        "condiciones_evaluadas": traceability.get(idx, []),
                    }

            # Guardar trazabilidad para filas NO clasificadas por esta regla
            unclassified_indices = df[unclassified_mask][~rule_mask].index
            for idx in unclassified_indices:
                # Inicializar si no existe
                if df.at[idx, "trazabilidad"] is None:
                    df.at[idx, "trazabilidad"] = {
                        "razon": "evaluando",
                        "estrategia_id": strategy.id,
                        "estrategia_nombre": strategy.name,
                        "reglas_evaluadas": [],
                    }

                # Agregar regla evaluada que NO cumplió
                if isinstance(df.at[idx, "trazabilidad"], dict):
                    if "reglas_evaluadas" not in df.at[idx, "trazabilidad"]:
                        df.at[idx, "trazabilidad"]["reglas_evaluadas"] = []

                    df.at[idx, "trazabilidad"]["reglas_evaluadas"].append(
                        {
                            "regla_id": rule.id,
                            "regla_nombre": rule.name,
                            "regla_prioridad": rule.priority,
                            "cumplida": False,
                            "condiciones": traceability.get(idx, []),
                        }
                    )

        # Clasificar filas restantes como REQUIERE_REVISION
        remaining_mask = df["clasificacion"].isna()
        if remaining_mask.any():
            df.loc[remaining_mask, "clasificacion"] = (
                TipoClasificacion.REQUIERE_REVISION.value
            )

            # Actualizar trazabilidad para registros sin clasificación
            for idx in df[remaining_mask].index:
                if df.at[idx, "trazabilidad"] is None:
                    df.at[idx, "trazabilidad"] = {}

                if isinstance(df.at[idx, "trazabilidad"], dict):
                    df.at[idx, "trazabilidad"]["razon"] = "requiere_revision"
                    df.at[idx, "trazabilidad"]["mensaje"] = (
                        f"Ninguna regla cumplió las condiciones. Total reglas evaluadas: {len(rules)}"
                    )

        return df

    def _get_strategy(
        self, id_enfermedad: int, use_cache: bool
    ) -> Optional[EstrategiaClasificacion]:
        """Obtiene la estrategia para un tipo de ENO."""
        if use_cache and id_enfermedad in self._cache:
            return self._cache[id_enfermedad]

        # Buscar estrategia activa
        result: Optional[EstrategiaClasificacion] = (
            self.session.execute(
                select(EstrategiaClasificacion)
                .where(EstrategiaClasificacion.id_enfermedad == id_enfermedad)
                .where(col(EstrategiaClasificacion.is_active).is_(True))
            )
            .scalars()
            .first()
        )

        if result and use_cache:
            self.session.refresh(
                result, ["classification_rules"]
            )  # Ensure relations are loaded
            self._cache[id_enfermedad] = result

        return result

    def _apply_strategy_config(
        self, df: pd.DataFrame, strategy: EstrategiaClasificacion
    ) -> pd.DataFrame:
        """Aplica configuración específica de la estrategia."""

        # Configuración de fechas si está definida
        if (
            strategy.config
            and isinstance(strategy.config, dict)
            and strategy.config.get("date_config")
        ):
            date_config = strategy.config["date_config"]

            # Aplicar configuración de fechas
            if "date_column" in date_config:
                date_col = date_config["date_column"]
                if date_col in df.columns:
                    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

        # Normalización de columnas si está definida
        if (
            strategy.config
            and isinstance(strategy.config, dict)
            and strategy.config.get("column_mapping")
        ):
            column_mapping = strategy.config["column_mapping"]

            # Renombrar columnas según mapeo
            df = df.rename(columns=column_mapping)

        return df

    def _apply_rule(self, df: pd.DataFrame, rule: ClassificationRule) -> pd.Series:
        """
        Evalúa una regla sobre un DataFrame.

        Args:
            df: DataFrame a evaluar
            rule: Regla a aplicar

        Returns:
            Serie booleana indicando qué filas cumplen la regla
        """
        # Si no hay condiciones, la regla aplica a todas las filas
        if not rule.filters:
            return pd.Series([True] * len(df), index=df.index)

        # Iniciar con máscara verdadera
        mask = pd.Series([True] * len(df), index=df.index)

        # Aplicar cada condición
        for condition in rule.filters:
            condition_mask = self._evaluate_condition(df, condition)

            # Combinar según operador lógico de la condición
            if condition.logical_operator == "AND":
                mask = mask & condition_mask
            elif condition.logical_operator == "OR":
                mask = mask | condition_mask
            else:
                # Por defecto, usar AND
                mask = mask & condition_mask

        return mask

    def _apply_rule_with_traceability(
        self, df: pd.DataFrame, rule: ClassificationRule
    ) -> tuple[pd.Series, Dict]:
        """
        Evalúa una regla sobre un DataFrame capturando información de trazabilidad.

        Args:
            df: DataFrame a evaluar
            rule: Regla a aplicar

        Returns:
            Tupla con (máscara booleana, diccionario de trazabilidad por índice)
        """
        # Diccionario para almacenar trazabilidad por índice de fila
        traceability: Dict[int, List[Dict[str, Any]]] = {}

        # Si no hay condiciones, la regla aplica a todas las filas
        if not rule.filters:
            for idx in df.index:
                traceability[idx] = [
                    {
                        "tipo": "sin_condiciones",
                        "resultado": True,
                        "mensaje": "Regla sin condiciones, aplica a todos los registros",
                    }
                ]
            return pd.Series([True] * len(df), index=df.index), traceability

        # Iniciar con máscara verdadera
        mask = pd.Series([True] * len(df), index=df.index)

        # Inicializar trazabilidad para cada fila
        for idx in df.index:
            traceability[idx] = []

        # Aplicar cada condición
        for condition in rule.filters:
            condition_mask = self._evaluate_condition(df, condition)

            # Capturar información de trazabilidad para cada fila
            config = condition.config if condition.config else {}
            for idx in df.index:
                condition_result = (
                    condition_mask.loc[idx] if idx in condition_mask.index else False
                )

                trace_item = {
                    "condicion_id": condition.id,
                    "campo": condition.field_name,
                    "tipo_filtro": condition.filter_type.value
                    if condition.filter_type
                    else "desconocido",
                    "operador_logico": condition.logical_operator,
                    "resultado": bool(condition_result),
                    "config": config,
                }

                # Agregar valor del campo si está disponible
                if condition.field_name in df.columns:
                    field_value = df.loc[idx, condition.field_name]
                    trace_item["valor_campo"] = (
                        str(field_value) if pd.notna(field_value) else None
                    )

                traceability[idx].append(trace_item)

            # Combinar según operador lógico de la condición
            if condition.logical_operator == "AND":
                mask = mask & condition_mask
            elif condition.logical_operator == "OR":
                mask = mask | condition_mask
            else:
                # Por defecto, usar AND
                mask = mask & condition_mask

        return mask, traceability

    def _evaluate_condition(
        self, df: pd.DataFrame, condition: FilterCondition
    ) -> pd.Series:
        """
        Evalúa una condición individual sobre un DataFrame.

        Args:
            df: DataFrame a evaluar
            condition: Condición a evaluar

        Returns:
            Serie booleana indicando qué filas cumplen la condición
        """
        # Verificar que la columna existe
        if condition.field_name not in df.columns:
            return pd.Series([False] * len(df), index=df.index)

        column = df[condition.field_name]

        # Obtener configuración del filtro
        config = condition.config if condition.config else {}

        # Evaluar según tipo de filtro
        if condition.filter_type == TipoFiltro.CAMPO_IGUAL:
            value = config.get("value", "")
            strict_mode = config.get("strict", False)

            if strict_mode:
                return column == value
            else:
                # Modo insensible por defecto
                normalized_value = self.normalize_text(str(value))
                return column.apply(
                    lambda x: self.normalize_text(str(x)) == normalized_value
                    if pd.notna(x)
                    else False
                )

        elif condition.filter_type == TipoFiltro.CAMPO_CONTIENE:
            value = config.get("value", "")
            strict_mode = config.get("strict", False)

            if column.dtype == "object":
                if strict_mode:
                    case_sensitive = config.get("case_sensitive", True)
                    return column.str.contains(value, na=False, case=case_sensitive)
                else:
                    # Modo insensible por defecto
                    normalized_value = self.normalize_text(str(value))
                    return column.apply(
                        lambda x: normalized_value in self.normalize_text(str(x))
                        if pd.notna(x)
                        else False
                    )
            return pd.Series([False] * len(df), index=df.index)

        elif condition.filter_type == TipoFiltro.CAMPO_EN_LISTA:
            # Obtener lista de valores desde config
            values = config.get("values", [])
            if not isinstance(values, list):
                # Si viene como string separado por comas (retrocompatibilidad)
                values = [v.strip() for v in str(values).split(",")]

            strict_mode = config.get("strict", False)

            if strict_mode:
                return column.isin(values)
            else:
                # Modo insensible por defecto - normalizar tanto valores como columna
                normalized_values = [self.normalize_text(str(v)) for v in values]
                return column.apply(
                    lambda x: self.normalize_text(str(x)) in normalized_values
                    if pd.notna(x)
                    else False
                )

        elif condition.filter_type == TipoFiltro.CAMPO_EXISTE:
            # Verificar que el campo tenga algún valor (no nulo y no vacío)
            return (
                column.notna() & (column != "") & (column.astype(str).str.strip() != "")
            )

        elif condition.filter_type == TipoFiltro.CAMPO_NO_NULO:
            return column.notna()

        elif condition.filter_type == TipoFiltro.REGEX_EXTRACCION:
            pattern = config.get("pattern", "")
            if column.dtype == "object" and pattern:
                try:
                    return column.str.match(pattern, na=False)
                except Exception:
                    return pd.Series([False] * len(df), index=df.index)
            return pd.Series([False] * len(df), index=df.index)

        elif condition.filter_type == TipoFiltro.CUSTOM_FUNCTION:
            # Para funciones personalizadas - por ahora no implementado
            return pd.Series([False] * len(df), index=df.index)

        elif condition.filter_type == TipoFiltro.DETECTOR_TIPO_SUJETO:
            # Para detector de tipo de sujeto - delegado a otro componente
            return pd.Series([False] * len(df), index=df.index)

        elif condition.filter_type == TipoFiltro.EXTRACTOR_METADATA:
            # Para extractor de metadata - no afecta la clasificación
            return pd.Series([False] * len(df), index=df.index)

        else:
            # Tipo de filtro no reconocido
            return pd.Series([False] * len(df), index=df.index)

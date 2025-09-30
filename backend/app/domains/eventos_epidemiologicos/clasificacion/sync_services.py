"""
Servicios síncronos para clasificación de eventos usando estrategias de DB.
"""

from typing import Dict, Optional

import pandas as pd
from sqlmodel import Session, select

from app.domains.eventos_epidemiologicos.clasificacion.models import (
    ClassificationRule,
    EventStrategy,
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
        self._cache: Dict[int, EventStrategy] = {}
    
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
        text = ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        
        # Reemplazar múltiples espacios por uno solo
        text = ' '.join(text.split())
        
        return text

    def classify_events(
        self, df: pd.DataFrame, tipo_eno_id: int, sample_ids: list = None, use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Clasifica eventos según la estrategia definida para un tipo de ENO.

        Args:
            df: DataFrame con los eventos a clasificar
            tipo_eno_id: ID del tipo de ENO
            sample_ids: Lista de IDs de eventos a loggear en detalle (opcional)
            use_cache: Si usar cache de estrategias

        Returns:
            DataFrame con columnas 'clasificacion' y 'es_positivo' agregadas
        """
        # Usar sample_ids si se provee, sino lista vacía
        target_cases = sample_ids if sample_ids else []
        has_target_event = False

        if target_cases and 'IDEVENTOCASO' in df.columns:
            has_target_event = df['IDEVENTOCASO'].isin(target_cases).any()

        if has_target_event:
            import logging
            logger = logging.getLogger(__name__)
            # Encontrar cuáles casos específicos están en este DataFrame
            current_targets = df[df['IDEVENTOCASO'].isin(target_cases)]['IDEVENTOCASO'].tolist()
            logger.error(f"🦟 SYNC SERVICE: Clasificando muestra {current_targets} con tipo_eno_id={tipo_eno_id}")
        
        # Obtener estrategia
        strategy = self._get_strategy(tipo_eno_id, use_cache)

        if not strategy:
            # Sin estrategia definida, marcar como sin clasificar
            if has_target_event:
                logger.error(f"🦟 SYNC SERVICE: No se encontró estrategia para tipo_eno_id={tipo_eno_id} - muestra afectada: {current_targets}")
            df["clasificacion"] = TipoClasificacion.REQUIERE_REVISION.value
            df["es_positivo"] = False
            return df

        if has_target_event:
            logger.error(f"🦟 SYNC SERVICE: Estrategia encontrada: {strategy.name} (ID: {strategy.id})")
            logger.error(f"🦟 SYNC SERVICE: Número de reglas: {len(strategy.classification_rules) if strategy.classification_rules else 0}")
            logger.error(f"🦟 SYNC SERVICE: Muestra a trackear: {current_targets}")

        # Aplicar configuración específica de la estrategia
        df = self._apply_strategy_config(df, strategy)

        # Inicializar columna de clasificación
        df["clasificacion"] = None
        df["es_positivo"] = False

        # Obtener reglas ordenadas por prioridad
        rules = sorted(
            [r for r in strategy.classification_rules if r.is_active],
            key=lambda r: r.priority,
        )

        if has_target_event:
            logger.error("🦟 SYNC SERVICE: Reglas activas ordenadas por prioridad:")
            for i, rule in enumerate(rules):
                logger.error(f"🦟 SYNC SERVICE:   {i+1}. {rule.name} (prioridad={rule.priority}, clasificación={rule.classification})")

        # Aplicar cada regla
        for rule_idx, rule in enumerate(rules):
            # Solo aplicar a filas aún no clasificadas
            unclassified_mask = df["clasificacion"].isna()
            if not unclassified_mask.any():
                if has_target_event:
                    logger.error("🦟 SYNC SERVICE: Todas las filas ya están clasificadas, terminando evaluación")
                break

            if has_target_event:
                unclassified_targets = df.loc[df['IDEVENTOCASO'].isin(target_cases) & df['clasificacion'].isna(), 'IDEVENTOCASO'].tolist()
                logger.error(f"🦟 SYNC SERVICE: Evaluando regla {rule_idx+1}: '{rule.name}' - Muestra sin clasificar: {unclassified_targets}")

            # Evaluar condiciones de la regla
            rule_mask = self._apply_rule(df[unclassified_mask].copy(), rule, target_cases)

            # Aplicar clasificación donde se cumple la regla
            indices = df[unclassified_mask][rule_mask].index

            if has_target_event:
                matched_targets = []
                if not indices.empty:
                    # Usar isin en los índices para encontrar los eventos de interés
                    matched_targets = df.loc[indices, 'IDEVENTOCASO'][df.loc[indices, 'IDEVENTOCASO'].isin(target_cases)].tolist()
                logger.error(f"🦟 SYNC SERVICE: Regla '{rule.name}' - {len(indices)} eventos cumplen, muestra incluida: {matched_targets}")

                if matched_targets:
                    logger.error(f"🦟 SYNC SERVICE: ✅ APLICANDO clasificación '{rule.classification}' a muestra: {matched_targets}")
            
            df.loc[indices, "clasificacion"] = rule.classification

            # Marcar como positivo si corresponde
            if rule.classification in [
                TipoClasificacion.CONFIRMADOS.value,
                TipoClasificacion.CON_RESULTADO_MORTAL.value,
            ]:
                df.loc[indices, "es_positivo"] = True

        # Clasificar filas restantes como REQUIERE_REVISION
        remaining_mask = df["clasificacion"].isna()
        df.loc[remaining_mask, "clasificacion"] = TipoClasificacion.REQUIERE_REVISION.value

        return df

    def _get_strategy(
        self, tipo_eno_id: int, use_cache: bool
    ) -> Optional[EventStrategy]:
        """Obtiene la estrategia para un tipo de ENO."""
        if use_cache and tipo_eno_id in self._cache:
            return self._cache[tipo_eno_id]

        # Buscar estrategia activa
        result = self.session.exec(
            select(EventStrategy)
            .where(EventStrategy.tipo_eno_id == tipo_eno_id)
            .where(EventStrategy.is_active == True)
        ).first()

        if result and use_cache:
            self._cache[tipo_eno_id] = result

        return result

    def _apply_strategy_config(
        self, df: pd.DataFrame, strategy: EventStrategy
    ) -> pd.DataFrame:
        """Aplica configuración específica de la estrategia."""

        # Configuración de fechas si está definida
        if strategy.config and isinstance(strategy.config, dict) and strategy.config.get("date_config"):
            date_config = strategy.config["date_config"]

            # Aplicar configuración de fechas
            if "date_column" in date_config:
                date_col = date_config["date_column"]
                if date_col in df.columns:
                    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

        # Normalización de columnas si está definida
        if strategy.config and isinstance(strategy.config, dict) and strategy.config.get("column_mapping"):
            column_mapping = strategy.config["column_mapping"]

            # Renombrar columnas según mapeo
            df = df.rename(columns=column_mapping)

        return df

    def _apply_rule(self, df: pd.DataFrame, rule: ClassificationRule, target_cases: list = None) -> pd.Series:
        """
        Evalúa una regla sobre un DataFrame.

        Args:
            df: DataFrame a evaluar
            rule: Regla a aplicar
            target_cases: Lista de IDs para logging (opcional)

        Returns:
            Serie booleana indicando qué filas cumplen la regla
        """
        # Detectar si tenemos eventos de interés
        has_target_event = False
        if target_cases and 'IDEVENTOCASO' in df.columns:
            has_target_event = df['IDEVENTOCASO'].isin(target_cases).any()

        # Si no hay condiciones, la regla aplica a todas las filas
        if not rule.filters:
            if has_target_event:
                import logging
                logger = logging.getLogger(__name__)
                current_targets = df[df['IDEVENTOCASO'].isin(target_cases)]['IDEVENTOCASO'].tolist()
                logger.error(f"🦟 RULE EVAL: Regla '{rule.name}' sin condiciones - aplica a todas las filas (incluye: {current_targets})")
            return pd.Series([True] * len(df), index=df.index)

        if has_target_event:
            import logging
            logger = logging.getLogger(__name__)
            current_targets = df[df['IDEVENTOCASO'].isin(target_cases)]['IDEVENTOCASO'].tolist()
            logger.error(f"🦟 RULE EVAL: Evaluando regla '{rule.name}' con {len(rule.filters)} condiciones para muestra: {current_targets}")

        # Iniciar con máscara verdadera
        mask = pd.Series([True] * len(df), index=df.index)

        # Aplicar cada condición
        for cond_idx, condition in enumerate(rule.filters):
            condition_mask = self._evaluate_condition(df, condition, target_cases)

            if has_target_event:
                matched_targets = []
                if not condition_mask.empty:
                    # Filtrar por eventos de interés usando el condition_mask
                    matched_targets = df.loc[condition_mask, 'IDEVENTOCASO'][df.loc[condition_mask, 'IDEVENTOCASO'].isin(target_cases)].tolist()
                config_value = condition.config.get('value') if condition.config else condition.config.get('values', 'No config') if condition.config else 'No config'
                logger.error(f"🦟 RULE EVAL:   Condición {cond_idx+1}: campo='{condition.field_name}', tipo='{condition.filter_type}', valor='{config_value}' - Muestra que cumple: {matched_targets}")

            # Combinar según operador lógico de la condición
            if condition.logical_operator == "AND":
                mask = mask & condition_mask
            elif condition.logical_operator == "OR":
                mask = mask | condition_mask
            else:
                # Por defecto, usar AND
                mask = mask & condition_mask

        if has_target_event:
            matched_targets = df.loc[mask, 'IDEVENTOCASO'][df.loc[mask, 'IDEVENTOCASO'].isin(target_cases)].tolist()
            logger.error(f"🦟 RULE EVAL: ✅ Resultado final regla '{rule.name}': Muestra que cumple: {matched_targets}")

        return mask

    def _evaluate_condition(
        self, df: pd.DataFrame, condition: FilterCondition, target_cases: list = None
    ) -> pd.Series:
        """
        Evalúa una condición individual sobre un DataFrame.

        Args:
            df: DataFrame a evaluar
            condition: Condición a evaluar
            target_cases: Lista de IDs para logging (opcional)

        Returns:
            Serie booleana indicando qué filas cumplen la condición
        """
        # Detectar si tenemos eventos de interés
        has_target_event = False
        if target_cases and 'IDEVENTOCASO' in df.columns:
            has_target_event = df['IDEVENTOCASO'].isin(target_cases).any()

        # Verificar que la columna existe
        if condition.field_name not in df.columns:
            if has_target_event:
                import logging
                logger = logging.getLogger(__name__)
                current_targets = df[df['IDEVENTOCASO'].isin(target_cases)]['IDEVENTOCASO'].tolist()
                logger.error(f"🦟 CONDITION: Campo '{condition.field_name}' no existe para muestra {current_targets} - retornando False")
            return pd.Series([False] * len(df), index=df.index)

        column = df[condition.field_name]

        # Obtener configuración del filtro
        config = condition.config if condition.config else {}

        if has_target_event:
            import logging
            logger = logging.getLogger(__name__)
            # Obtener el valor específico del campo para los eventos de interés
            target_values = {}
            for event_id in target_cases:
                if (df['IDEVENTOCASO'] == event_id).any():
                    target_values[event_id] = df.loc[df['IDEVENTOCASO'] == event_id, condition.field_name].iloc[0]
            config_value = config.get('value') or config.get('values', 'No config')
            logger.error(f"🦟 CONDITION: Campo='{condition.field_name}', Valores muestra={target_values}, Buscando='{config_value}', Tipo='{condition.filter_type}'")

        # Evaluar según tipo de filtro
        if condition.filter_type == TipoFiltro.CAMPO_IGUAL:
            value = config.get('value', '')
            strict_mode = config.get('strict', False)
            
            if strict_mode:
                return column == value
            else:
                # Modo insensible por defecto
                normalized_value = self.normalize_text(str(value))
                return column.apply(lambda x: self.normalize_text(str(x)) == normalized_value if pd.notna(x) else False)

        elif condition.filter_type == TipoFiltro.CAMPO_CONTIENE:
            value = config.get('value', '')
            strict_mode = config.get('strict', False)
            
            if column.dtype == "object":
                if strict_mode:
                    case_sensitive = config.get('case_sensitive', True)
                    return column.str.contains(value, na=False, case=case_sensitive)
                else:
                    # Modo insensible por defecto
                    normalized_value = self.normalize_text(str(value))
                    return column.apply(lambda x: normalized_value in self.normalize_text(str(x)) if pd.notna(x) else False)
            return pd.Series([False] * len(df), index=df.index)

        elif condition.filter_type == TipoFiltro.CAMPO_EN_LISTA:
            # Obtener lista de valores desde config
            values = config.get('values', [])
            if not isinstance(values, list):
                # Si viene como string separado por comas (retrocompatibilidad)
                values = [v.strip() for v in str(values).split(",")]
            
            strict_mode = config.get('strict', False)
            
            if strict_mode:
                return column.isin(values)
            else:
                # Modo insensible por defecto - normalizar tanto valores como columna
                normalized_values = [self.normalize_text(str(v)) for v in values]
                return column.apply(lambda x: self.normalize_text(str(x)) in normalized_values if pd.notna(x) else False)

        elif condition.filter_type == TipoFiltro.CAMPO_EXISTE:
            # Verificar que el campo tenga algún valor (no nulo y no vacío)
            return column.notna() & (column != "") & (column.astype(str).str.strip() != "")

        elif condition.filter_type == TipoFiltro.CAMPO_NO_NULO:
            return column.notna()

        elif condition.filter_type == TipoFiltro.REGEX_EXTRACCION:
            pattern = config.get('pattern', '')
            if column.dtype == "object" and pattern:
                try:
                    return column.str.match(pattern, na=False)
                except:
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

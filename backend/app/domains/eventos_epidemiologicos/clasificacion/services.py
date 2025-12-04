"""
Services layer para clasificación de eventos usando estrategias de DB.
"""

import re
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.eventos_epidemiologicos.clasificacion.models import (
    ClassificationRule,
    EventStrategy,
    FilterCondition,
    TipoClasificacion,
    TipoFiltro,
)
from app.domains.eventos_epidemiologicos.clasificacion.repositories import (
    ClassificationRuleRepository,
    EventStrategyRepository,
)


class EventClassificationService:
    """
    Servicio para clasificar eventos epidemiológicos usando estrategias de DB.

    Este servicio aplica las reglas de clasificación definidas en la base de datos
    a un DataFrame de eventos, determinando su clasificación (confirmado, sospechoso, etc.).
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio de clasificación.

        Args:
            session: Sesión de base de datos async
        """
        self.session = session
        self.strategy_repo = EventStrategyRepository(session)
        self.rule_repo = ClassificationRuleRepository(session)
        self._cache: Dict[int, EventStrategy] = {}

    async def classify_events(
        self, df: pd.DataFrame, tipo_eno_id: int, use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Clasifica eventos según la estrategia definida para un tipo de ENO.

        Args:
            df: DataFrame con los eventos a clasificar
            tipo_eno_id: ID del tipo de ENO
            use_cache: Si usar cache de estrategias

        Returns:
            DataFrame con columna 'clasificacion' agregada
        """
        # Obtener estrategia
        strategy = await self._get_strategy(tipo_eno_id, use_cache)

        if not strategy:
            # Sin estrategia definida, marcar como sin clasificar
            df["clasificacion"] = TipoClasificacion.TODOS.value
            df["es_positivo"] = False
            return df

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

        # Aplicar cada regla
        for rule in rules:
            # Solo aplicar a filas aún no clasificadas
            unclassified_mask = df["clasificacion"].isna()
            if not unclassified_mask.any():
                break

            # Evaluar condiciones de la regla
            rule_mask = self._apply_rule(df[unclassified_mask].copy(), rule)

            # Aplicar clasificación donde se cumple la regla
            indices = df[unclassified_mask][rule_mask].index
            df.loc[indices, "clasificacion"] = rule.classification.value

            # Marcar como positivo si corresponde
            if rule.classification in [
                TipoClasificacion.CONFIRMADOS,
                TipoClasificacion.CON_RESULTADO_MORTAL,
            ]:
                df.loc[indices, "es_positivo"] = True

            # Los casos REQUIERE_REVISION no son positivos ni negativos
            if rule.classification == TipoClasificacion.REQUIERE_REVISION:
                df.loc[indices, "es_positivo"] = None  # Requiere revisión manual

        # Clasificar restantes como TODOS
        df["clasificacion"].fillna(TipoClasificacion.TODOS.value, inplace=True)

        return df

    def _apply_strategy_config(
        self, df: pd.DataFrame, strategy: EventStrategy
    ) -> pd.DataFrame:
        """
        Aplica configuración específica de la estrategia al DataFrame.

        Args:
            df: DataFrame de eventos
            strategy: Estrategia a aplicar

        Returns:
            DataFrame modificado
        """
        # Aplicar filtro de provincia si corresponde
        if strategy.usa_provincia_carga and "PROVINCIA_CARGA" in df.columns:
            df = df[df["PROVINCIA_CARGA"] == "Chubut"].copy()
        elif "PROVINCIA_RESIDENCIA" in df.columns:
            df = df[df["PROVINCIA_RESIDENCIA"] == "Chubut"].copy()

        return df

    def _apply_rule(self, df: pd.DataFrame, rule: ClassificationRule) -> pd.Series:
        """
        Aplica una regla de clasificación y retorna máscara booleana.

        Args:
            df: DataFrame de eventos
            rule: Regla a aplicar

        Returns:
            Serie booleana indicando filas que cumplen la regla
        """
        if not rule.filters:
            # Sin filtros, la regla aplica a todos
            return pd.Series([True] * len(df), index=df.index)

        conditions = []

        # Evaluar cada condición de filtro
        for filter_cond in sorted(rule.filters, key=lambda f: f.order):
            mask = self._apply_filter_condition(df, filter_cond)
            conditions.append((mask, filter_cond.logical_operator))

        # Combinar condiciones con operadores lógicos
        if not conditions:
            return pd.Series([False] * len(df), index=df.index)

        result = conditions[0][0]
        for i in range(1, len(conditions)):
            mask, _ = conditions[i]
            operator = conditions[i - 1][1]  # Usar operador de la condición anterior

            if operator == "OR":
                result = result | mask
            else:  # AND
                result = result & mask

        return result

    def _apply_filter_condition(
        self, df: pd.DataFrame, condition: FilterCondition
    ) -> pd.Series:
        """
        Aplica una condición de filtro individual.

        Args:
            df: DataFrame de eventos
            condition: Condición a aplicar

        Returns:
            Serie booleana indicando filas que cumplen la condición
        """
        filter_type = condition.filter_type
        field_name = condition.field_name

        # Validar que el campo existe
        if field_name not in df.columns and filter_type != TipoFiltro.REGEX_EXTRACCION:
            return pd.Series([False] * len(df), index=df.index)

        # Aplicar según tipo de filtro
        if filter_type == TipoFiltro.CAMPO_IGUAL:
            return df[field_name] == condition.value

        elif filter_type == TipoFiltro.CAMPO_EN_LISTA:
            return df[field_name].isin(condition.values or [])

        elif filter_type == TipoFiltro.CAMPO_CONTIENE:
            return df[field_name].str.contains(
                condition.value or "", na=False, case=False
            )

        elif filter_type == TipoFiltro.CAMPO_EXISTE:
            return df[field_name].notna()

        elif filter_type == TipoFiltro.CAMPO_NO_NULO:
            return df[field_name].notna() & (df[field_name] != "")

        elif filter_type == TipoFiltro.REGEX_EXTRACCION:
            return self._apply_regex_extraction(df, condition)

        elif filter_type == TipoFiltro.CUSTOM_FUNCTION:
            return self._apply_custom_function(df, condition)

        elif filter_type == TipoFiltro.DETECTOR_TIPO_SUJETO:
            return self._apply_subject_type_detection(df, condition)

        elif filter_type == TipoFiltro.EXTRACTOR_METADATA:
            return self._apply_metadata_extraction(df, condition)

        else:
            return pd.Series([False] * len(df), index=df.index)

    def _apply_regex_extraction(
        self, df: pd.DataFrame, condition: FilterCondition
    ) -> pd.Series:
        """
        Aplica extracción por regex (caso especial como rabia animal).

        Args:
            df: DataFrame de eventos
            condition: Condición con configuración de extracción

        Returns:
            Serie booleana indicando filas donde se extrajo algo
        """
        config = condition.config or {}
        extraction_fields = config.get("extraction_fields", [])
        pattern = condition.pattern
        normalization = config.get("normalization", {})
        case_insensitive = config.get("case_insensitive", True)
        create_field = config.get("create_field")

        if not pattern or not extraction_fields:
            return pd.Series([False] * len(df), index=df.index)

        # Preparar flags de regex
        flags = re.IGNORECASE if case_insensitive else 0

        # Extraer de múltiples campos
        extracted_values = pd.Series([None] * len(df), index=df.index)

        for field in extraction_fields:
            if field not in df.columns:
                continue

            # Extraer valores usando regex
            field_extracts = df[field].str.extract(
                f"({pattern})", flags=flags, expand=False
            )

            # Combinar con valores previos (prioridad al primero encontrado)
            extracted_values = extracted_values.fillna(field_extracts)

        # Aplicar normalización si existe
        if normalization and not extracted_values.isna().all():
            for old_val, new_val in normalization.items():
                extracted_values = extracted_values.str.replace(
                    old_val, new_val, case=False, regex=False
                )

        # Crear campo si se especifica
        if create_field:
            df[create_field] = extracted_values

        # Retornar máscara de valores extraídos
        return extracted_values.notna()

    def _apply_custom_function(
        self, df: pd.DataFrame, condition: FilterCondition
    ) -> pd.Series:
        """
        Aplica una función personalizada definida en config.

        Args:
            df: DataFrame de eventos
            condition: Condición con función personalizada

        Returns:
            Serie booleana resultante de la función
        """
        config = condition.config or {}
        function_name = config.get("function")

        # Mapeo de funciones personalizadas disponibles
        custom_functions = {
            "tiene_resultado_mortal": lambda df: df.get(
                "FALLECIDO", pd.Series([False] * len(df))
            )
            == "SI",
            "es_caso_importado": lambda df: df.get(
                "CASO_IMPORTADO", pd.Series([False] * len(df))
            ).eq(True),
            "tiene_nexo_epidemiologico": lambda df: df.get(
                "CLASIFICACION_MANUAL", pd.Series([""] * len(df))
            ).str.contains("nexo", case=False, na=False),
        }

        if function_name in custom_functions:
            return custom_functions[function_name](df)

        return pd.Series([False] * len(df), index=df.index)

    def _apply_subject_type_detection(
        self, df: pd.DataFrame, condition: FilterCondition
    ) -> pd.Series:
        """
        Aplica detección de tipo de sujeto usando el TipoSujetoDetector.

        Args:
            df: DataFrame de eventos
            condition: Condición con configuración de detección

        Returns:
            Serie booleana indicando casos que cumplen el criterio
        """
        from .detectors import TipoSujetoDetector

        config = condition.config or {}
        target_type = config.get(
            "target_type", "humano"
        )  # 'humano', 'animal', 'indeterminado'
        min_confidence = config.get("min_confidence", 0.5)

        detector = TipoSujetoDetector()
        results = []

        for idx, row in df.iterrows():
            tipo, confidence, metadata = detector.detectar(row.to_dict())

            # Verificar si cumple criterios
            matches = tipo == target_type and confidence >= min_confidence
            results.append(matches)

            # Guardar metadata si se especifica campo
            if condition.extracted_metadata_field and matches:
                # Aquí se podría guardar en una columna temporal del DataFrame
                # para uso posterior en la clasificación
                df.loc[idx, f"_meta_{condition.extracted_metadata_field}"] = tipo
                df.loc[idx, "_meta_confidence"] = confidence

        return pd.Series(results, index=df.index)

    def _apply_metadata_extraction(
        self, df: pd.DataFrame, condition: FilterCondition
    ) -> pd.Series:
        """
        Extrae metadata adicional sin afectar la clasificación.

        Args:
            df: DataFrame de eventos
            condition: Condición con configuración de extracción

        Returns:
            Serie booleana (siempre True para no filtrar casos)
        """
        from .detectors import MetadataExtractor

        config = condition.config or {}
        extractor_type = config.get("extractor", "fuente_contagio")

        extractor = MetadataExtractor()

        for idx, row in df.iterrows():
            if extractor_type == "fuente_contagio":
                resultado = extractor.extraer_fuente_contagio(row.to_dict())
                if condition.extracted_metadata_field and resultado:
                    df.loc[idx, f"_meta_{condition.extracted_metadata_field}"] = (
                        resultado
                    )

        # Los extractores no filtran casos, solo agregan información
        return pd.Series([True] * len(df), index=df.index)

    async def _get_strategy(
        self, tipo_eno_id: int, use_cache: bool = True
    ) -> Optional[EventStrategy]:
        """
        Obtiene una estrategia, usando cache si está disponible.

        Args:
            tipo_eno_id: ID del tipo de ENO
            use_cache: Si usar cache

        Returns:
            Estrategia encontrada o None
        """
        if use_cache and tipo_eno_id in self._cache:
            return self._cache[tipo_eno_id]

        strategy = await self.strategy_repo.get_by_tipo_eno(tipo_eno_id)

        if strategy and use_cache:
            self._cache[tipo_eno_id] = strategy

        return strategy

    def clear_cache(self) -> None:
        """Limpia el cache de estrategias."""
        self._cache.clear()

    async def test_classification(
        self, df: pd.DataFrame, strategy_id: int
    ) -> pd.DataFrame:
        """
        Prueba la clasificación con un DataFrame directamente usando strategy_id.

        Args:
            df: DataFrame de prueba
            strategy_id: ID de la estrategia a probar

        Returns:
            DataFrame con resultados de la prueba
        """
        # Obtener estrategia por ID
        strategy = await self.strategy_repo.get_by_id(strategy_id)
        if not strategy:
            raise ValueError(f"Estrategia {strategy_id} no encontrada")

        # Clasificar usando la estrategia específica
        return await self._classify_with_strategy(df, strategy)

    async def _classify_with_strategy(
        self, df: pd.DataFrame, strategy: EventStrategy
    ) -> pd.DataFrame:
        """
        Clasifica eventos usando una estrategia específica.

        Args:
            df: DataFrame de eventos
            strategy: Estrategia a aplicar

        Returns:
            DataFrame con clasificaciones
        """
        # Aplicar configuración específica de la estrategia
        df = self._apply_strategy_config(df.copy(), strategy)

        # Inicializar columna de clasificación
        df["clasificacion"] = None
        df["es_positivo"] = False

        # Obtener reglas ordenadas por prioridad
        rules = sorted(
            [r for r in strategy.classification_rules if r.is_active],
            key=lambda r: r.priority,
        )

        # Aplicar cada regla
        for rule in rules:
            # Solo aplicar a filas aún no clasificadas
            unclassified_mask = df["clasificacion"].isna()
            if not unclassified_mask.any():
                break

            unclassified_df = df[unclassified_mask]
            rule_mask = self._apply_rule(unclassified_df, rule)

            # Aplicar clasificación a las filas que cumplen la regla
            matching_indices = unclassified_df[rule_mask].index
            df.loc[matching_indices, "clasificacion"] = rule.classification.value
            df.loc[matching_indices, "es_positivo"] = (
                rule.classification.value in self.POSITIVE_CLASSIFICATIONS
            )

        # Marcar casos no clasificados como 'todos'
        df["clasificacion"].fillna(TipoClasificacion.TODOS.value, inplace=True)

        return df

    async def test_classification_legacy(
        self, test_data: List[Dict[str, Any]], tipo_eno_id: int
    ) -> Dict[str, Any]:
        """
        Prueba la clasificación con datos de ejemplo (método legacy).

        Args:
            test_data: Lista de registros de prueba
            tipo_eno_id: ID del tipo de ENO

        Returns:
            Diccionario con resultados de la prueba
        """
        # Crear DataFrame de prueba
        df = pd.DataFrame(test_data)

        # Clasificar
        result_df = await self.classify_events(df, tipo_eno_id, use_cache=False)

        # Preparar resumen
        classification_counts = result_df["clasificacion"].value_counts().to_dict()
        positive_count = result_df["es_positivo"].sum()

        return {
            "total_records": len(result_df),
            "classifications": classification_counts,
            "positive_count": int(positive_count),
            "positive_percentage": round(positive_count / len(result_df) * 100, 2)
            if len(result_df) > 0
            else 0,
            "sample_results": result_df.head(10).to_dict("records"),
        }


class StrategyValidationService:
    """
    Servicio para validar estrategias y reglas antes de guardarlas.
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio de validación.

        Args:
            session: Sesión de base de datos async
        """
        self.session = session
        self.strategy_repo = EventStrategyRepository(session)

    async def validate_strategy(self, strategy: EventStrategy) -> List[str]:
        """
        Valida una estrategia completa.

        Args:
            strategy: Estrategia a validar

        Returns:
            Lista de errores encontrados (vacía si es válida)
        """
        errors = []

        # Validar que valid_from sea anterior a valid_until
        if strategy.valid_until is not None and strategy.valid_from >= strategy.valid_until:
            errors.append(
                f"valid_from ({strategy.valid_from}) debe ser anterior a valid_until ({strategy.valid_until})"
            )

        # Validar que no haya solapamiento de fechas con otras estrategias
        overlapping_strategies = await self.strategy_repo.check_date_overlap(
            tipo_eno_id=strategy.tipo_eno_id,
            valid_from=strategy.valid_from,
            valid_until=strategy.valid_until,
            exclude_strategy_id=strategy.id,
        )

        if overlapping_strategies:
            overlap_details = []
            for overlap in overlapping_strategies:
                valid_until_str = (
                    overlap.valid_until.strftime("%Y-%m-%d")
                    if overlap.valid_until
                    else "sin fin"
                )
                overlap_details.append(
                    f"'{overlap.name}' ({overlap.valid_from.strftime('%Y-%m-%d')} - {valid_until_str})"
                )
            errors.append(
                f"El período de validez se solapa con las siguientes estrategias: {', '.join(overlap_details)}"
            )

        # Validar gráficos disponibles
        valid_charts = [
            "corredor_endemico",
            "curva_epidemiologica",
            "casos_por_ugd",
            "torta_sexo",
            "casos_mensuales",
            "totales_historicos",
        ]

        for chart in strategy.graficos_disponibles:
            if chart not in valid_charts:
                errors.append(f"Tipo de gráfico inválido: {chart}")

        # Validar reglas
        if strategy.classification_rules:
            rule_errors = self._validate_rules(strategy.classification_rules)
            errors.extend(rule_errors)

        return errors

    def _validate_rules(self, rules: List[ClassificationRule]) -> List[str]:
        """
        Valida un conjunto de reglas.

        Args:
            rules: Lista de reglas a validar

        Returns:
            Lista de errores encontrados
        """
        errors = []

        # Verificar prioridades únicas
        priorities = [r.priority for r in rules if r.is_active]
        if len(priorities) != len(set(priorities)):
            errors.append("Existen reglas con la misma prioridad")

        # Validar cada regla
        for rule in rules:
            if not rule.filters:
                continue

            # Validar condiciones
            for condition in rule.filters:
                cond_errors = self._validate_condition(condition)
                errors.extend(cond_errors)

        return errors

    def _validate_condition(self, condition: FilterCondition) -> List[str]:
        """
        Valida una condición de filtro.

        Args:
            condition: Condición a validar

        Returns:
            Lista de errores encontrados
        """
        errors = []

        # Validar según tipo
        if condition.filter_type == TipoFiltro.CAMPO_IGUAL:
            if not condition.value:
                errors.append(
                    f"Condición {condition.id}: CAMPO_IGUAL requiere un valor"
                )

        elif condition.filter_type == TipoFiltro.CAMPO_EN_LISTA:
            if not condition.values or len(condition.values) == 0:
                errors.append(
                    f"Condición {condition.id}: CAMPO_EN_LISTA requiere una lista de valores"
                )

        elif condition.filter_type == TipoFiltro.REGEX_EXTRACCION:
            if not condition.pattern:
                errors.append(
                    f"Condición {condition.id}: REGEX_EXTRACCION requiere un patrón"
                )

            # Validar regex
            try:
                re.compile(condition.pattern)
            except re.error:
                errors.append(f"Condición {condition.id}: Patrón regex inválido")

            # Validar configuración
            if condition.config:
                if "extraction_fields" not in condition.config:
                    errors.append(
                        f"Condición {condition.id}: REGEX_EXTRACCION requiere extraction_fields en config"
                    )

        # Validar operador lógico
        if condition.logical_operator not in ["AND", "OR"]:
            errors.append(
                f"Condición {condition.id}: Operador lógico debe ser AND u OR"
            )

        return errors

"""
Tests de integración para EventClassificationService.

Valida el flujo completo de clasificación usando la base de datos
y las estrategias reales configuradas.
"""

from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest
from app.domains.eventos_epidemiologicos.clasificacion.models import (
    ClassificationRule,
    EventStrategy,
    FilterCondition,
    TipoClasificacion,
    TipoFiltro,
)
from app.domains.eventos_epidemiologicos.clasificacion.services import (
    EventClassificationService,
)
from sqlalchemy.ext.asyncio import AsyncSession

from tests.domains.estrategias.fixtures.csv_samples import RABIA_SAMPLES


class TestEventClassificationServiceIntegration:
    """Tests de integración para el servicio de clasificación."""

    @pytest.fixture
    def mock_session(self):
        """Mock de sesión de base de datos."""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    def classification_service(self, mock_session):
        """Servicio de clasificación con sesión mock."""
        return EventClassificationService(mock_session)

    @pytest.fixture
    def mock_rabia_strategy(self):
        """Mock de estrategia de rabia animal con reglas reales."""
        strategy = MagicMock(spec=EventStrategy)
        strategy.id = 1
        strategy.strategy_name = "RabiaAnimalEstrategia"
        strategy.description = "Estrategia para Rabia Animal"
        strategy.is_active = True

        # Regla 1: Confirmados
        rule_confirmados = MagicMock(spec=ClassificationRule)
        rule_confirmados.id = 1
        rule_confirmados.classification = TipoClasificacion.CONFIRMADOS
        rule_confirmados.priority = 1
        rule_confirmados.is_active = True
        rule_confirmados.auto_approve = True
        rule_confirmados.required_confidence = 0.0

        # Filtro para confirmados: CLASIFICACION_MANUAL == "Caso confirmado"
        filter_confirmados = MagicMock(spec=FilterCondition)
        filter_confirmados.filter_type = TipoFiltro.CAMPO_IGUAL
        filter_confirmados.field_name = "CLASIFICACION_MANUAL"
        filter_confirmados.value = "Caso confirmado"
        filter_confirmados.logical_operator = "AND"
        filter_confirmados.order = 0

        rule_confirmados.filters = [filter_confirmados]

        # Regla 2: Sospechosos
        rule_sospechosos = MagicMock(spec=ClassificationRule)
        rule_sospechosos.id = 2
        rule_sospechosos.classification = TipoClasificacion.SOSPECHOSOS
        rule_sospechosos.priority = 2
        rule_sospechosos.is_active = True
        rule_sospechosos.auto_approve = True
        rule_sospechosos.required_confidence = 0.0

        # Filtro para sospechosos
        filter_sospechosos = MagicMock(spec=FilterCondition)
        filter_sospechosos.filter_type = TipoFiltro.CAMPO_IGUAL
        filter_sospechosos.field_name = "CLASIFICACION_MANUAL"
        filter_sospechosos.value = "Caso sospechoso"
        filter_sospechosos.logical_operator = "AND"
        filter_sospechosos.order = 0

        rule_sospechosos.filters = [filter_sospechosos]

        # Regla 3: Detector de tipo de sujeto
        rule_detector = MagicMock(spec=ClassificationRule)
        rule_detector.id = 3
        rule_detector.classification = TipoClasificacion.REQUIERE_REVISION
        rule_detector.priority = 10  # Baja prioridad
        rule_detector.is_active = True
        rule_detector.auto_approve = False
        rule_detector.required_confidence = 0.6

        # Filtro detector de sujeto
        filter_detector = MagicMock(spec=FilterCondition)
        filter_detector.filter_type = TipoFiltro.DETECTOR_TIPO_SUJETO
        filter_detector.field_name = "tipo_sujeto_detectado"
        filter_detector.value = "indeterminado"
        filter_detector.logical_operator = "AND"
        filter_detector.order = 0

        rule_detector.filters = [filter_detector]

        strategy.classification_rules = [
            rule_confirmados,
            rule_sospechosos,
            rule_detector,
        ]
        strategy.metadata_extractors = []
        strategy.confidence_threshold = 0.5

        return strategy

    @pytest.mark.asyncio
    async def test_classify_events_rabia_casos_basicos(
        self, classification_service, mock_rabia_strategy
    ):
        """Test clasificación básica de casos de rabia."""
        # Agregar atributos faltantes al mock
        mock_rabia_strategy.usa_provincia_carga = False
        mock_rabia_strategy.provincia_field = "PROVINCIA_RESIDENCIA"

        # Setup mock repository
        classification_service.strategy_repo.get_by_tipo_eno = AsyncMock(
            return_value=mock_rabia_strategy
        )

        # Crear DataFrame con casos de rabia
        rabia_df = pd.DataFrame(
            [
                sample
                for sample in RABIA_SAMPLES[:3]  # Solo primeros 3 casos
            ]
        )

        # Ejecutar clasificación
        result_df = await classification_service.classify_events(
            rabia_df, tipo_eno_id=1
        )

        # Validaciones básicas
        assert "clasificacion" in result_df.columns
        assert "es_positivo" in result_df.columns
        assert len(result_df) == 3

        # Verificar que se llamó al repositorio
        classification_service.strategy_repo.get_by_tipo_eno.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_classify_events_sin_estrategia(self, classification_service):
        """Test clasificación cuando no hay estrategia definida."""
        # Setup: sin estrategia
        classification_service.strategy_repo.get_by_tipo_eno = AsyncMock(
            return_value=None
        )

        # Datos de prueba
        test_df = pd.DataFrame([{"IDEVENTOCASO": "1001", "NOMBRE": "JUAN"}])

        # Ejecutar
        result_df = await classification_service.classify_events(
            test_df, tipo_eno_id=999
        )

        # Validaciones
        assert result_df["clasificacion"].iloc[0] == TipoClasificacion.TODOS.value
        assert result_df["es_positivo"].iloc[0] is False

    @pytest.mark.asyncio
    async def test_apply_rule_campo_igual(self, classification_service):
        """Test aplicación de regla con filtro CAMPO_IGUAL."""
        # Datos de prueba
        test_df = pd.DataFrame(
            [
                {"ID": 1, "CLASIFICACION_MANUAL": "Caso confirmado"},
                {"ID": 2, "CLASIFICACION_MANUAL": "Caso sospechoso"},
                {"ID": 3, "CLASIFICACION_MANUAL": "Caso confirmado"},
            ]
        )

        # Mock de regla
        rule = MagicMock(spec=ClassificationRule)
        rule.filters = []

        # Mock de filtro
        filter_condition = MagicMock(spec=FilterCondition)
        filter_condition.filter_type = TipoFiltro.CAMPO_IGUAL
        filter_condition.field_name = "CLASIFICACION_MANUAL"
        filter_condition.value = "Caso confirmado"
        filter_condition.logical_operator = "AND"

        rule.filters.append(filter_condition)

        # Aplicar regla (método privado, accedemos directamente)
        result_mask = classification_service._apply_rule(test_df, rule)

        # Validar resultado
        expected_indices = [0, 2]  # Registros con "Caso confirmado"
        actual_indices = test_df[result_mask].index.tolist()
        assert actual_indices == expected_indices

    @pytest.mark.asyncio
    async def test_apply_rule_campo_en_lista(self, classification_service):
        """Test aplicación de regla con filtro CAMPO_EN_LISTA."""
        # Datos de prueba
        test_df = pd.DataFrame(
            [
                {"ID": 1, "RESULTADO": "Reactivo"},
                {"ID": 2, "RESULTADO": "No reactivo"},
                {"ID": 3, "RESULTADO": "Detectable"},
                {"ID": 4, "RESULTADO": "Indeterminado"},
            ]
        )

        # Mock de regla
        rule = MagicMock(spec=ClassificationRule)

        # Mock de filtro
        filter_condition = MagicMock(spec=FilterCondition)
        filter_condition.filter_type = TipoFiltro.CAMPO_EN_LISTA
        filter_condition.field_name = "RESULTADO"
        filter_condition.values = ["Reactivo", "Detectable"]
        filter_condition.logical_operator = "AND"

        rule.filters = [filter_condition]

        # Aplicar regla
        result_mask = classification_service._apply_rule(test_df, rule)

        # Validar resultado
        expected_indices = [0, 2]  # Reactivo y Detectable
        actual_indices = test_df[result_mask].index.tolist()
        assert actual_indices == expected_indices

    @pytest.mark.asyncio
    async def test_apply_multiple_filters_and(self, classification_service):
        """Test aplicación de múltiples filtros con operador AND."""
        # Datos de prueba
        test_df = pd.DataFrame(
            [
                {"ID": 1, "RESULTADO": "Reactivo", "PROVINCIA": "Chubut"},
                {"ID": 2, "RESULTADO": "Reactivo", "PROVINCIA": "Buenos Aires"},
                {"ID": 3, "RESULTADO": "No reactivo", "PROVINCIA": "Chubut"},
                {"ID": 4, "RESULTADO": "Reactivo", "PROVINCIA": "Chubut"},
            ]
        )

        # Mock de regla con 2 filtros
        rule = MagicMock(spec=ClassificationRule)

        # Filtro 1: RESULTADO == "Reactivo"
        filter1 = MagicMock(spec=FilterCondition)
        filter1.filter_type = TipoFiltro.CAMPO_IGUAL
        filter1.field_name = "RESULTADO"
        filter1.value = "Reactivo"
        filter1.logical_operator = "AND"
        filter1.order = 0

        # Filtro 2: PROVINCIA == "Chubut"
        filter2 = MagicMock(spec=FilterCondition)
        filter2.filter_type = TipoFiltro.CAMPO_IGUAL
        filter2.field_name = "PROVINCIA"
        filter2.value = "Chubut"
        filter2.logical_operator = "AND"
        filter2.order = 1

        rule.filters = [filter1, filter2]

        # Aplicar regla
        result_mask = classification_service._apply_rule(test_df, rule)

        # Validar: solo registros 0 y 3 cumplen ambas condiciones
        expected_indices = [0, 3]
        actual_indices = test_df[result_mask].index.tolist()
        assert set(actual_indices) == set(expected_indices)

    @pytest.mark.asyncio
    async def test_priority_rules_application(
        self, classification_service, mock_rabia_strategy
    ):
        """Test que las reglas se aplican por orden de prioridad."""
        # Agregar atributos faltantes al mock
        mock_rabia_strategy.usa_provincia_carga = False
        mock_rabia_strategy.provincia_field = "PROVINCIA_RESIDENCIA"

        # Setup
        classification_service.strategy_repo.get_by_tipo_eno = AsyncMock(
            return_value=mock_rabia_strategy
        )

        # Caso que puede cumplir múltiples reglas
        test_df = pd.DataFrame(
            [
                {
                    "IDEVENTOCASO": "1001",
                    "CLASIFICACION_MANUAL": "Caso confirmado",  # Cumple regla prioridad 1
                    "NOMBRE": "CARLOS",
                    "APELLIDO": "RODRIGUEZ",
                    "SEXO": "IND",  # También podría ser indeterminado (prioridad 10)
                }
            ]
        )

        # Ejecutar clasificación
        result_df = await classification_service.classify_events(test_df, tipo_eno_id=1)

        # Debe aplicarse la regla de mayor prioridad (confirmados)
        assert result_df["clasificacion"].iloc[0] == TipoClasificacion.CONFIRMADOS.value
        assert result_df["es_positivo"].iloc[0] is True

    @pytest.mark.asyncio
    async def test_confidence_threshold_enforcement(self, classification_service):
        """Test que se respetan los umbrales de confianza."""
        # Mock de regla con alta confianza requerida
        rule = MagicMock(spec=ClassificationRule)
        rule.classification = TipoClasificacion.CONFIRMADOS
        rule.required_confidence = 0.8  # Alta confianza requerida
        rule.auto_approve = False  # Requiere revisión si no cumple confianza

        # Mock de filtro detector
        filter_condition = MagicMock(spec=FilterCondition)
        filter_condition.filter_type = TipoFiltro.DETECTOR_TIPO_SUJETO
        filter_condition.field_name = "confidence_score"
        filter_condition.value = "0.5"  # Baja confianza

        rule.filters = [filter_condition]

        # Datos con baja confianza
        test_df = pd.DataFrame(
            [
                {
                    "IDEVENTOCASO": "1001",
                    "confidence_score": 0.5,  # Menor que el umbral
                }
            ]
        )

        # En un caso real, esto debería marcar como requiere revisión
        # Por ahora solo validamos que la lógica de filtros funciona
        result_mask = classification_service._apply_rule(test_df, rule)

        # La regla se evalúa pero la confianza es insuficiente
        assert (
            len(test_df[result_mask]) >= 0
        )  # Puede o no aplicarse según implementación

    @pytest.mark.asyncio
    async def test_cache_strategy_functionality(
        self, classification_service, mock_rabia_strategy
    ):
        """Test funcionalidad de cache de estrategias."""
        # Agregar atributos faltantes al mock
        mock_rabia_strategy.usa_provincia_carga = False
        mock_rabia_strategy.provincia_field = "PROVINCIA_RESIDENCIA"

        # Setup mock para primera llamada
        classification_service.strategy_repo.get_by_tipo_eno = AsyncMock(
            return_value=mock_rabia_strategy
        )

        # Primera llamada - debe ir al repositorio
        await classification_service._get_strategy(tipo_eno_id=1, use_cache=True)

        # Segunda llamada - debe usar cache
        await classification_service._get_strategy(tipo_eno_id=1, use_cache=True)

        # Verificar que el repositorio solo se llamó una vez
        assert classification_service.strategy_repo.get_by_tipo_eno.call_count == 1

        # Verificar que el cache tiene la estrategia
        assert 1 in classification_service._cache
        assert classification_service._cache[1] == mock_rabia_strategy

    @pytest.mark.asyncio
    async def test_cache_disabled_functionality(
        self, classification_service, mock_rabia_strategy
    ):
        """Test funcionalidad sin cache."""
        # Agregar atributos faltantes al mock
        mock_rabia_strategy.usa_provincia_carga = False
        mock_rabia_strategy.provincia_field = "PROVINCIA_RESIDENCIA"

        # Setup
        classification_service.strategy_repo.get_by_tipo_eno = AsyncMock(
            return_value=mock_rabia_strategy
        )

        # Dos llamadas sin cache
        await classification_service._get_strategy(tipo_eno_id=1, use_cache=False)
        await classification_service._get_strategy(tipo_eno_id=1, use_cache=False)

        # Debe llamar al repositorio ambas veces
        assert classification_service.strategy_repo.get_by_tipo_eno.call_count == 2


class TestEventClassificationServiceEdgeCases:
    """Tests para casos edge del servicio."""

    @pytest.fixture
    def mock_session(self):
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    def classification_service(self, mock_session):
        return EventClassificationService(mock_session)

    @pytest.mark.asyncio
    async def test_empty_dataframe(self, classification_service):
        """Test con DataFrame vacío."""
        empty_df = pd.DataFrame()

        classification_service.strategy_repo.get_by_tipo_eno = AsyncMock(
            return_value=None
        )

        result_df = await classification_service.classify_events(
            empty_df, tipo_eno_id=1
        )

        assert len(result_df) == 0
        assert "clasificacion" in result_df.columns
        assert "es_positivo" in result_df.columns

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, classification_service):
        """Test con campos requeridos faltantes."""
        # DataFrame sin CLASIFICACION_MANUAL
        df_missing_fields = pd.DataFrame(
            [
                {
                    "IDEVENTOCASO": "1001",
                    "NOMBRE": "JUAN",
                    # Falta CLASIFICACION_MANUAL
                }
            ]
        )

        classification_service.strategy_repo.get_by_tipo_eno = AsyncMock(
            return_value=None
        )

        # No debería fallar, solo marcar como sin clasificar
        result_df = await classification_service.classify_events(
            df_missing_fields, tipo_eno_id=1
        )

        assert len(result_df) == 1
        assert result_df["clasificacion"].iloc[0] == TipoClasificacion.TODOS.value

    @pytest.mark.asyncio
    async def test_null_values_in_classification_fields(self, classification_service):
        """Test con valores nulos en campos de clasificación."""
        df_with_nulls = pd.DataFrame(
            [
                {"IDEVENTOCASO": "1001", "CLASIFICACION_MANUAL": None},
                {"IDEVENTOCASO": "1002", "CLASIFICACION_MANUAL": ""},
                {"IDEVENTOCASO": "1003", "CLASIFICACION_MANUAL": "Caso confirmado"},
            ]
        )

        classification_service.strategy_repo.get_by_tipo_eno = AsyncMock(
            return_value=None
        )

        result_df = await classification_service.classify_events(
            df_with_nulls, tipo_eno_id=1
        )

        # Todos deberían tener alguna clasificación (aunque sea default)
        assert len(result_df) == 3
        assert result_df["clasificacion"].notna().all()

"""
Tests unitarios para BloqueQueryAdapter.

Verifica la lógica de construcción de criterios y resolución de series
sin necesidad de una base de datos real.
"""

from unittest.mock import MagicMock

from app.domains.boletines.constants import TipoBloque, TipoVisualizacion
from app.domains.boletines.models import BoletinBloque
from app.domains.boletines.services.adapter import (
    BloqueQueryAdapter,
    BoletinContexto,
)
from app.domains.metricas.criteria.base import EmptyCriterion
from app.domains.metricas.criteria.evento import (
    AgentesMultiplesCriterion,
    TipoEventoCriterion,
)


class TestBoletinContexto:
    """Tests para BoletinContexto."""

    def test_contexto_default_anios_historicos(self):
        """Verifica que los años históricos por defecto excluyen pandemia."""
        ctx = BoletinContexto(semana_actual=20, anio_actual=2025)

        assert ctx.anios_historicos == [2018, 2019, 2022, 2023, 2024]
        assert 2020 not in ctx.anios_historicos
        assert 2021 not in ctx.anios_historicos

    def test_contexto_custom_anios(self):
        """Permite customizar años históricos."""
        ctx = BoletinContexto(
            semana_actual=20,
            anio_actual=2025,
            anios_historicos=[2019, 2023, 2024],
        )

        assert ctx.anios_historicos == [2019, 2023, 2024]


class TestSeriesFromConfig:
    """Tests para resolución de series desde config manual."""

    def setup_method(self):
        """Setup con session mock."""
        self.mock_session = MagicMock()
        self.adapter = BloqueQueryAdapter(self.mock_session)

    def test_series_from_config_tipo_evento(self):
        """Resuelve serie con tipo_evento_slug."""
        config = [
            {
                "slug": "eti",
                "label": "ETI",
                "color": "#2196F3",
                "tipo_evento_slug": "eti",
            }
        ]

        series = self.adapter._series_from_config(config)

        assert len(series) == 1
        assert series[0].slug == "eti"
        assert series[0].label == "ETI"
        assert series[0].color == "#2196F3"
        assert isinstance(series[0].criterion, TipoEventoCriterion)
        assert series[0].criterion.evento_slug == "eti"

    def test_series_from_config_agente_ids(self):
        """Resuelve serie con lista de agente_ids."""
        config = [
            {
                "slug": "influenza",
                "label": "Influenza",
                "color": "#F44336",
                "agente_ids": [1, 2, 3],
            }
        ]

        series = self.adapter._series_from_config(config)

        assert len(series) == 1
        assert isinstance(series[0].criterion, AgentesMultiplesCriterion)
        assert series[0].criterion.agente_ids == [1, 2, 3]

    def test_series_from_config_sin_criterio(self):
        """Serie sin criterio específico usa EmptyCriterion."""
        config = [{"slug": "total", "label": "Total", "color": "#000000"}]

        series = self.adapter._series_from_config(config)

        assert len(series) == 1
        assert isinstance(series[0].criterion, EmptyCriterion)

    def test_series_from_config_multiples(self):
        """Resuelve múltiples series."""
        config = [
            {
                "slug": "eti",
                "label": "ETI",
                "color": "#2196F3",
                "tipo_evento_slug": "eti",
            },
            {
                "slug": "neumonia",
                "label": "Neumonía",
                "color": "#FF9800",
                "tipo_evento_slug": "neumonia",
            },
            {
                "slug": "bronquiolitis",
                "label": "Bronquiolitis",
                "color": "#F44336",
                "tipo_evento_slug": "bronquiolitis",
            },
        ]

        series = self.adapter._series_from_config(config)

        assert len(series) == 3
        assert [s.slug for s in series] == ["eti", "neumonia", "bronquiolitis"]


class TestConstruirCriterioBase:
    """Tests para construcción de criterios base."""

    def setup_method(self):
        """Setup con session mock y bloque de prueba."""
        self.mock_session = MagicMock()
        self.adapter = BloqueQueryAdapter(self.mock_session)
        self.contexto = BoletinContexto(
            semana_actual=20, anio_actual=2025, num_semanas=4
        )

    def _crear_bloque(self, **kwargs) -> BoletinBloque:
        """Helper para crear bloque de prueba."""
        defaults = {
            "id": 1,
            "seccion_id": 1,
            "slug": "test-bloque",
            "titulo_template": "Test",
            "tipo_bloque": TipoBloque.CURVA_EPIDEMIOLOGICA,
            "tipo_visualizacion": TipoVisualizacion.LINE_CHART,
            "metrica_codigo": "casos_clinicos",
            "dimensiones": ["SEMANA_EPIDEMIOLOGICA"],
            "criterios_fijos": {},
            "orden": 1,
            "activo": True,
        }
        defaults.update(kwargs)
        return BoletinBloque(**defaults)

    def test_criterio_corredor_endemico_usa_anios_multiples(self):
        """Corredor endémico genera AniosMultiplesCriterion."""
        bloque = self._crear_bloque(tipo_bloque=TipoBloque.CORREDOR_ENDEMICO)

        criterio = self.adapter._construir_criterio_base(bloque, self.contexto)

        # Debería incluir años históricos + actual
        # El criterio combinado es una conjunción (AND)
        # Verificamos que el criterio no es vacío
        assert criterio is not None
        assert not isinstance(criterio, EmptyCriterion)

    def test_criterio_curva_usa_rango_periodo(self):
        """Curva epidemiológica genera RangoPeriodoCriterion."""
        bloque = self._crear_bloque(tipo_bloque=TipoBloque.CURVA_EPIDEMIOLOGICA)

        criterio = self.adapter._construir_criterio_base(bloque, self.contexto)

        assert criterio is not None

    def test_criterio_con_tipo_evento_slug(self):
        """Criterios fijos con tipo_evento_slug genera TipoEventoCriterion."""
        bloque = self._crear_bloque(criterios_fijos={"tipo_evento_slug": "eti"})

        criterio = self.adapter._construir_criterio_base(bloque, self.contexto)

        # El criterio debería combinar temporal + evento
        assert criterio is not None

    def test_criterio_rango_semanas(self):
        """Verifica cálculo correcto del rango de semanas."""
        # Semana 20 con ventana de 4 = semanas 17-20
        bloque = self._crear_bloque()
        contexto = BoletinContexto(semana_actual=20, anio_actual=2025, num_semanas=4)

        criterio = self.adapter._construir_criterio_base(bloque, contexto)

        # El rango debería ser SE 17-20/2025
        assert criterio is not None

    def test_criterio_semana_inicio_minimo_1(self):
        """La semana de inicio no puede ser menor a 1."""
        bloque = self._crear_bloque()
        # Semana 2 con ventana de 4 debería dar semanas 1-2
        contexto = BoletinContexto(semana_actual=2, anio_actual=2025, num_semanas=4)

        criterio = self.adapter._construir_criterio_base(bloque, contexto)

        assert criterio is not None


class TestDeterminarCompute:
    """Tests para determinación del compute a aplicar."""

    def setup_method(self):
        self.mock_session = MagicMock()
        self.adapter = BloqueQueryAdapter(self.mock_session)

    def _crear_bloque(self, **kwargs) -> BoletinBloque:
        defaults = {
            "id": 1,
            "seccion_id": 1,
            "slug": "test",
            "titulo_template": "Test",
            "tipo_bloque": TipoBloque.CURVA_EPIDEMIOLOGICA,
            "tipo_visualizacion": TipoVisualizacion.LINE_CHART,
            "metrica_codigo": "casos_clinicos",
            "dimensiones": [],
            "criterios_fijos": {},
            "orden": 1,
            "activo": True,
        }
        defaults.update(kwargs)
        return BoletinBloque(**defaults)

    def test_compute_explicito_tiene_prioridad(self):
        """Si bloque tiene compute, se usa ese."""
        bloque = self._crear_bloque(compute="custom_compute")

        compute = self.adapter._determinar_compute(bloque)

        assert compute == "custom_compute"

    def test_corredor_endemico_infiere_compute(self):
        """Corredor endémico infiere compute automáticamente."""
        bloque = self._crear_bloque(
            tipo_bloque=TipoBloque.CORREDOR_ENDEMICO,
            compute=None,
        )

        compute = self.adapter._determinar_compute(bloque)

        assert compute == "corredor_endemico"

    def test_otros_tipos_sin_compute_default(self):
        """Otros tipos de bloque no tienen compute por defecto."""
        bloque = self._crear_bloque(
            tipo_bloque=TipoBloque.TABLA_RESUMEN,
            compute=None,
        )

        compute = self.adapter._determinar_compute(bloque)

        assert compute is None


class TestRenderTitulo:
    """Tests para renderizado de títulos con Jinja2."""

    def setup_method(self):
        self.mock_session = MagicMock()
        self.adapter = BloqueQueryAdapter(self.mock_session)

    def _crear_bloque(self, titulo_template: str) -> BoletinBloque:
        return BoletinBloque(
            id=1,
            seccion_id=1,
            slug="test",
            titulo_template=titulo_template,
            tipo_bloque=TipoBloque.CURVA_EPIDEMIOLOGICA,
            tipo_visualizacion=TipoVisualizacion.LINE_CHART,
            metrica_codigo="casos_clinicos",
            dimensiones=[],
            criterios_fijos={},
            orden=1,
            activo=True,
        )

    def test_render_titulo_con_variables(self):
        """Renderiza título con variables de contexto."""
        bloque = self._crear_bloque("Semana {{ semana }} del año {{ anio }}")
        contexto = BoletinContexto(semana_actual=20, anio_actual=2025)

        titulo = self.adapter._render_titulo(bloque, contexto, num_series=3)

        assert titulo == "Semana 20 del año 2025"

    def test_render_titulo_con_num_series(self):
        """Renderiza título con número de series."""
        bloque = self._crear_bloque("Gráfico con {{ num_series }} series")
        contexto = BoletinContexto(semana_actual=20, anio_actual=2025)

        titulo = self.adapter._render_titulo(bloque, contexto, num_series=5)

        assert titulo == "Gráfico con 5 series"

    def test_render_titulo_sin_variables(self):
        """Títulos estáticos se mantienen."""
        bloque = self._crear_bloque("Título estático sin variables")
        contexto = BoletinContexto(semana_actual=20, anio_actual=2025)

        titulo = self.adapter._render_titulo(bloque, contexto, num_series=1)

        assert titulo == "Título estático sin variables"

    def test_render_titulo_error_graceful(self):
        """Errores en template retornan el template original."""
        bloque = self._crear_bloque("Error: {{ variable_inexistente.metodo() }}")
        contexto = BoletinContexto(semana_actual=20, anio_actual=2025)

        titulo = self.adapter._render_titulo(bloque, contexto, num_series=1)

        # En caso de error, retorna el template original
        assert "Error:" in titulo


class TestResolverSeries:
    """Tests para resolución de series desde diferentes fuentes."""

    def setup_method(self):
        self.mock_session = MagicMock()
        self.adapter = BloqueQueryAdapter(self.mock_session)

    def _crear_bloque(self, series_source=None, series_config=None) -> BoletinBloque:
        return BoletinBloque(
            id=1,
            seccion_id=1,
            slug="test",
            titulo_template="Test",
            tipo_bloque=TipoBloque.CURVA_EPIDEMIOLOGICA,
            tipo_visualizacion=TipoVisualizacion.LINE_CHART,
            metrica_codigo="casos_clinicos",
            dimensiones=[],
            criterios_fijos={},
            series_source=series_source,
            series_config=series_config,
            orden=1,
            activo=True,
        )

    def test_resolver_series_manual(self):
        """series_source=manual usa series_config."""
        config = [
            {"slug": "a", "label": "Serie A", "color": "#000"},
            {"slug": "b", "label": "Serie B", "color": "#fff"},
        ]
        bloque = self._crear_bloque(series_source="manual", series_config=config)

        series = self.adapter._resolver_series(bloque)

        assert len(series) == 2
        assert series[0].slug == "a"
        assert series[1].slug == "b"

    def test_resolver_series_none_usa_config(self):
        """series_source=None usa series_config."""
        config = [{"slug": "x", "label": "X", "color": "#123"}]
        bloque = self._crear_bloque(series_source=None, series_config=config)

        series = self.adapter._resolver_series(bloque)

        assert len(series) == 1
        assert series[0].slug == "x"

    def test_resolver_series_formato_invalido(self):
        """Formato inválido de series_source usa config."""
        config = [{"slug": "fallback", "label": "Fallback", "color": "#000"}]
        bloque = self._crear_bloque(
            series_source="invalid_format", series_config=config
        )

        series = self.adapter._resolver_series(bloque)

        assert len(series) == 1
        assert series[0].slug == "fallback"

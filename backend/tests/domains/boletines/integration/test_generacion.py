"""
Tests de integración para generación de boletines.

Estos tests requieren una base de datos real con datos de ejemplo.
Usan la misma configuración que la aplicación.
"""

import os

import pytest

# Skip si no hay DB configurada
pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"), reason="Requiere DATABASE_URL configurada"
)


def get_session():
    """Obtiene sesión de BD desde la app."""
    from app.core.database import get_session_local

    session = get_session_local()
    try:
        yield session
    finally:
        session.close()


class TestGeneracionConDatosReales:
    """
    Tests de integración que verifican generación con datos reales.

    Para ejecutar estos tests:
    1. Asegúrate de tener DATABASE_URL configurada
    2. Ejecuta: pytest tests/domains/boletines/integration/ -v
    """

    def test_metric_service_query_casos_clinicos(self):
        """Verifica que MetricService puede consultar casos clínicos."""
        from app.core.database import get_session_local
        from app.domains.metricas.criteria.temporal import RangoPeriodoCriterion
        from app.domains.metricas.service import MetricService

        session = get_session_local()
        try:
            service = MetricService(session)

            # Query simple de casos clínicos
            result = service.query(
                metric="casos_clinicos",
                dimensions=["SEMANA_EPIDEMIOLOGICA"],
                criteria=RangoPeriodoCriterion(
                    anio_desde=2024,
                    semana_desde=1,
                    anio_hasta=2024,
                    semana_hasta=10,
                ),
            )

            assert "data" in result
            assert "metadata" in result
            assert result["metadata"]["metric"] == "casos_clinicos"

        finally:
            session.close()

    def test_corredor_endemico_compute(self):
        """Verifica cálculo de corredor endémico."""
        from app.core.database import get_session_local
        from app.domains.metricas.criteria.temporal import AniosMultiplesCriterion
        from app.domains.metricas.service import MetricService

        session = get_session_local()
        try:
            service = MetricService(session)

            # Query con compute corredor_endemico
            result = service.query(
                metric="casos_clinicos",
                dimensions=["SEMANA_EPIDEMIOLOGICA", "ANIO_EPIDEMIOLOGICO"],
                criteria=AniosMultiplesCriterion(
                    anios=[2018, 2019, 2022, 2023, 2024, 2025]
                ),
                compute="corredor_endemico",
                filters={"periodo": {"anio": 2025, "semana": 20}},
            )

            assert "data" in result

            # Si hay datos, verificar estructura del corredor
            if result["data"]:
                row = result["data"][0]
                # El corredor debe tener estas columnas
                expected_keys = ["semana_epidemiologica", "valor_actual"]
                for key in expected_keys:
                    assert key in row, f"Falta columna {key} en resultado corredor"

        finally:
            session.close()

    def test_bloque_query_adapter_ejecutar(self):
        """Verifica que BloqueQueryAdapter puede ejecutar un bloque."""
        from app.core.database import get_session_local
        from app.domains.boletines.constants import TipoBloque, TipoVisualizacion
        from app.domains.boletines.models import BoletinBloque
        from app.domains.boletines.services.adapter import (
            BloqueQueryAdapter,
            BoletinContexto,
        )

        session = get_session_local()
        try:
            adapter = BloqueQueryAdapter(session)
            contexto = BoletinContexto(
                semana_actual=20, anio_actual=2025, num_semanas=4
            )

            # Crear bloque de prueba (sin persistir)
            bloque = BoletinBloque(
                id=999,
                seccion_id=1,
                slug="test-integracion",
                titulo_template="Test SE {{ semana }}",
                tipo_bloque=TipoBloque.CURVA_EPIDEMIOLOGICA,
                tipo_visualizacion=TipoVisualizacion.LINE_CHART,
                metrica_codigo="casos_clinicos",
                dimensiones=["SEMANA_EPIDEMIOLOGICA"],
                criterios_fijos={},
                series_config=[{"slug": "total", "label": "Total", "color": "#000"}],
                config_visual={},
                orden=1,
                activo=True,
            )

            resultado = adapter.ejecutar_bloque(bloque, contexto)

            assert resultado.slug == "test-integracion"
            assert resultado.titulo == "Test SE 20"
            assert isinstance(resultado.series, list)

        finally:
            session.close()


class TestSeedSecciones:
    """Tests para verificar el seed de secciones y bloques."""

    def test_seed_crea_secciones(self):
        """Verifica que el seed crea secciones correctamente."""
        from sqlmodel import select

        from app.core.database import get_session_local
        from app.domains.boletines.models import BoletinSeccion

        session = get_session_local()
        try:
            # Ejecutar seed
            from app.domains.boletines.seeds.secciones_bloques import (
                seed_secciones_y_bloques,
            )

            seed_secciones_y_bloques(session)

            # Verificar que existen secciones
            stmt = select(BoletinSeccion).where(BoletinSeccion.activo.is_(True))
            secciones = session.execute(stmt).scalars().all()

            assert len(secciones) > 0, "El seed debería crear secciones"

            # Verificar secciones específicas
            slugs = [s.slug for s in secciones]
            assert "ira" in slugs, "Debe existir sección IRA"
            assert "diarreas" in slugs, "Debe existir sección Diarreas"

        finally:
            session.rollback()  # No persistir cambios de test
            session.close()

    def test_seed_crea_bloques(self):
        """Verifica que el seed crea bloques correctamente."""
        from sqlmodel import select

        from app.core.database import get_session_local
        from app.domains.boletines.models import BoletinBloque

        session = get_session_local()
        try:
            from app.domains.boletines.seeds.secciones_bloques import (
                seed_secciones_y_bloques,
            )

            seed_secciones_y_bloques(session)

            stmt = select(BoletinBloque).where(BoletinBloque.activo.is_(True))
            bloques = session.execute(stmt).scalars().all()

            assert len(bloques) > 0, "El seed debería crear bloques"

            # Verificar bloques específicos
            slugs = [b.slug for b in bloques]
            assert "corredor-eti" in slugs, "Debe existir bloque corredor ETI"

        finally:
            session.rollback()
            session.close()

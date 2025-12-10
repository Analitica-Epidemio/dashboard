"""
Tests unitarios para BoletinGenerator.

Verifica la generación de boletines y estructura TipTap.
"""

from unittest.mock import MagicMock

from app.domains.boletines.constants import TipoBloque, TipoVisualizacion
from app.domains.boletines.models import BoletinBloque, BoletinSeccion
from app.domains.boletines.services.generator import BoletinGenerator


class TestBoletinGenerator:
    """Tests para BoletinGenerator."""

    def setup_method(self):
        """Setup con mocks."""
        self.mock_session = MagicMock()
        # Mock para que commit/refresh funcionen
        self.mock_session.add = MagicMock()
        self.mock_session.commit = MagicMock()
        self.mock_session.refresh = MagicMock()

    def _crear_seccion(
        self, slug: str, titulo: str, orden: int, bloques: list = None
    ) -> BoletinSeccion:
        """Helper para crear sección de prueba."""
        seccion = BoletinSeccion(
            id=orden,
            slug=slug,
            titulo=titulo,
            orden=orden,
            activo=True,
        )
        seccion.bloques = bloques or []
        return seccion

    def _crear_bloque(self, slug: str, titulo: str, orden: int) -> BoletinBloque:
        """Helper para crear bloque de prueba."""
        return BoletinBloque(
            id=orden,
            seccion_id=1,
            slug=slug,
            titulo_template=titulo,
            tipo_bloque=TipoBloque.CURVA_EPIDEMIOLOGICA,
            tipo_visualizacion=TipoVisualizacion.LINE_CHART,
            metrica_codigo="casos_clinicos",
            dimensiones=["SEMANA_EPIDEMIOLOGICA"],
            criterios_fijos={},
            config_visual={},
            orden=orden,
            activo=True,
        )


class TestCrearPortada:
    """Tests para generación de portada."""

    def setup_method(self):
        self.mock_session = MagicMock()
        self.generator = BoletinGenerator(self.mock_session)

    def test_portada_contiene_titulo(self):
        """La portada incluye título principal."""
        from app.domains.boletines.services.adapter import BoletinContexto

        ctx = BoletinContexto(semana_actual=20, anio_actual=2025)
        portada = self.generator._crear_portada(ctx)

        # Debe ser una lista de nodos TipTap
        assert isinstance(portada, list)
        assert len(portada) > 0

        # Primer elemento es heading nivel 1
        assert portada[0]["type"] == "heading"
        assert portada[0]["attrs"]["level"] == 1

    def test_portada_incluye_semana_y_anio(self):
        """La portada muestra semana y año."""
        from app.domains.boletines.services.adapter import BoletinContexto

        ctx = BoletinContexto(semana_actual=40, anio_actual=2025)
        portada = self.generator._crear_portada(ctx)

        # Buscar texto que contenga semana y año
        textos = self._extraer_textos(portada)
        texto_completo = " ".join(textos)

        assert "40" in texto_completo
        assert "2025" in texto_completo

    def _extraer_textos(self, nodos: list) -> list[str]:
        """Extrae todos los textos de una estructura TipTap."""
        textos = []
        for nodo in nodos:
            if nodo.get("type") == "text":
                textos.append(nodo.get("text", ""))
            if "content" in nodo:
                textos.extend(self._extraer_textos(nodo["content"]))
        return textos


class TestCrearMetodologia:
    """Tests para sección de metodología."""

    def setup_method(self):
        self.mock_session = MagicMock()
        self.generator = BoletinGenerator(self.mock_session)

    def test_metodologia_contiene_fuente(self):
        """La metodología menciona SNVS."""
        metodologia = self.generator._crear_metodologia()

        textos = self._extraer_textos(metodologia)
        texto_completo = " ".join(textos)

        assert "SNVS" in texto_completo

    def test_metodologia_menciona_anios_corredor(self):
        """La metodología explica años usados para corredor."""
        metodologia = self.generator._crear_metodologia()

        textos = self._extraer_textos(metodologia)
        texto_completo = " ".join(textos)

        # Debe mencionar que se excluyen años de pandemia
        assert "2018" in texto_completo or "pandemia" in texto_completo.lower()

    def _extraer_textos(self, nodos: list) -> list[str]:
        textos = []
        for nodo in nodos:
            if nodo.get("type") == "text":
                textos.append(nodo.get("text", ""))
            if "content" in nodo:
                textos.extend(self._extraer_textos(nodo["content"]))
        return textos


class TestBloqueToTiptap:
    """Tests para conversión de bloques a TipTap."""

    def setup_method(self):
        self.mock_session = MagicMock()
        self.generator = BoletinGenerator(self.mock_session)

    def test_bloque_genera_dynamic_block(self):
        """Los bloques generan nodos dynamicBlock."""
        from app.domains.boletines.services.adapter import BloqueResultado

        resultado = BloqueResultado(
            bloque_id=1,
            slug="test-bloque",
            titulo="Test Título",
            tipo_visualizacion="line_chart",
            series=[{"serie": "Serie A", "slug": "a", "color": "#000", "data": []}],
            config_visual={"height": 400},
            metadata={"tipo_bloque": "curva_epidemiologica"},
        )

        tiptap = self.generator._bloque_to_tiptap(resultado)

        assert tiptap["type"] == "dynamicBlock"
        assert tiptap["attrs"]["blockId"] == "test-bloque"
        assert tiptap["attrs"]["titulo"] == "Test Título"
        assert "data" in tiptap["attrs"]

    def test_bloque_incluye_series_en_data(self):
        """El nodo dynamicBlock incluye datos de series."""
        from app.domains.boletines.services.adapter import BloqueResultado

        series_data = [
            {
                "serie": "ETI",
                "slug": "eti",
                "color": "#2196F3",
                "data": [{"semana": 1, "valor": 100}],
            },
            {
                "serie": "Neumonía",
                "slug": "neumonia",
                "color": "#FF9800",
                "data": [{"semana": 1, "valor": 50}],
            },
        ]

        resultado = BloqueResultado(
            bloque_id=1,
            slug="ira-series",
            titulo="IRA",
            tipo_visualizacion="stacked_bar",
            series=series_data,
            config_visual={},
            metadata={},
        )

        tiptap = self.generator._bloque_to_tiptap(resultado)

        assert tiptap["attrs"]["data"]["series"] == series_data


class TestCrearDocumentoTiptap:
    """Tests para generación del documento TipTap completo."""

    def setup_method(self):
        self.mock_session = MagicMock()
        self.generator = BoletinGenerator(self.mock_session)

    def test_documento_tiene_estructura_doc(self):
        """El documento tiene type=doc."""
        from app.domains.boletines.services.adapter import BoletinContexto

        ctx = BoletinContexto(semana_actual=20, anio_actual=2025)
        secciones = []

        doc = self.generator._crear_documento_tiptap(secciones, ctx)

        assert doc["type"] == "doc"
        assert "content" in doc
        assert isinstance(doc["content"], list)

    def test_documento_incluye_portada_y_metodologia(self):
        """El documento incluye portada al inicio y metodología al final."""
        from app.domains.boletines.services.adapter import BoletinContexto

        ctx = BoletinContexto(semana_actual=20, anio_actual=2025)
        secciones = []

        doc = self.generator._crear_documento_tiptap(secciones, ctx)
        content = doc["content"]

        # Primer elemento debería ser heading (de portada)
        assert content[0]["type"] == "heading"

        # Último heading debería ser metodología
        headings = [n for n in content if n.get("type") == "heading"]
        ultimo_heading_texto = self._get_heading_text(headings[-1])
        assert "metodolog" in ultimo_heading_texto.lower()

    def test_documento_incluye_secciones(self):
        """El documento incluye las secciones proporcionadas."""
        from app.domains.boletines.services.adapter import BoletinContexto

        ctx = BoletinContexto(semana_actual=20, anio_actual=2025)
        secciones = [
            {
                "slug": "ira",
                "titulo": "Vigilancia de IRA",
                "contenido_intro": None,
                "bloques": [],
            }
        ]

        doc = self.generator._crear_documento_tiptap(secciones, ctx)
        content = doc["content"]

        # Buscar heading con título de sección
        headings = [n for n in content if n.get("type") == "heading"]
        titulos = [self._get_heading_text(h) for h in headings]

        assert "Vigilancia de IRA" in titulos

    def _get_heading_text(self, heading: dict) -> str:
        """Extrae texto de un nodo heading."""
        if "content" in heading:
            for node in heading["content"]:
                if node.get("type") == "text":
                    return node.get("text", "")
        return ""

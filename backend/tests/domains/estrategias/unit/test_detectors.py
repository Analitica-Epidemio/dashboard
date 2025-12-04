"""
Tests unitarios para detectores inteligentes de tipo de sujeto.
"""

import pytest

from app.domains.eventos_epidemiologicos.clasificacion.detectors import (
    MetadataExtractor,
    TipoSujetoDetector,
)


class TestTipoSujetoDetector:
    """Tests para el detector de tipo de sujeto sin hardcodeo de especies."""

    def setup_method(self):
        """Setup para cada test."""
        self.detector = TipoSujetoDetector()

    def test_detecta_humano_con_documento_valido(self):
        """Test caso claro: humano con documento válido."""
        row = {
            "NOMBRE": "JUAN",
            "APELLIDO": "PEREZ",
            "SEXO": "M",
            "TIPO_DOC": "DNI",
            "NRO_DOC": "12345678",
        }

        tipo, confidence, metadata = self.detector.detectar(row)

        assert tipo == "humano"
        assert confidence >= 0.7  # Alta confianza
        assert "nombre_completo" in metadata
        assert metadata["nombre_completo"] == "JUAN PEREZ"
        assert "documento" in metadata

    def test_detecta_humano_con_sexo_definido(self):
        """Test humano con sexo masculino/femenino."""
        row = {
            "NOMBRE": "MARIA",
            "APELLIDO": "GONZALEZ",
            "SEXO": "F",
            "TIPO_DOC": "LC",
            "NRO_DOC": "87654321",
        }

        tipo, confidence, metadata = self.detector.detectar(row)

        assert tipo == "humano"
        assert confidence >= 0.7
        assert metadata["nombre"] == "MARIA"
        assert metadata["apellido"] == "GONZALEZ"

    def test_detecta_animal_con_nomenclatura_cientifica(self):
        """Test animal con nombre científico típico."""
        row = {
            "NOMBRE": "TADARIDA",
            "APELLIDO": "BRASILIENSIS",
            "SEXO": "IND",
            "TIPO_DOC": "",
            "NRO_DOC": "",
        }

        tipo, confidence, metadata = self.detector.detectar(row)

        assert tipo == "animal"
        assert confidence >= 0.5
        assert "especie" in metadata
        assert "subespecie" in metadata
        assert "clasificacion_taxonomica" in metadata
        assert metadata["clasificacion_taxonomica"]["genero"] == "TADARIDA"
        assert metadata["clasificacion_taxonomica"]["especie"] == "BRASILIENSIS"

    def test_detecta_animal_con_nn(self):
        """Test animal con nombre genérico 'NN'."""
        row = {
            "NOMBRE": "NN",
            "APELLIDO": "MURCIELAGO",
            "SEXO": "IND",
            "TIPO_DOC": "",
            "NRO_DOC": "",
        }

        tipo, confidence, metadata = self.detector.detectar(row)

        assert tipo == "animal"
        assert confidence >= 0.5
        assert metadata["especie"] == "MURCIELAGO"

    def test_detecta_animal_con_ubicacion_en_apellido(self):
        """Test animal con información de ubicación en apellido."""
        row = {
            "NOMBRE": "ZORRO",
            "APELLIDO": "RUTA 25 KM 1234",
            "SEXO": "ND",
            "TIPO_DOC": "",
            "NRO_DOC": "",
        }

        tipo, confidence, metadata = self.detector.detectar(row)

        assert tipo == "animal"
        assert confidence >= 0.5
        assert metadata["especie"] == "ZORRO"
        assert metadata["ubicacion"] == "RUTA 25 KM 1234"

    def test_detecta_animal_con_patron_taxonomico(self):
        """Test detección por patrones taxonómicos sin hardcodear especies."""
        row = {
            "NOMBRE": "HISTIOTUS",
            "APELLIDO": "MONTANUS",
            "SEXO": "ND",
            "TIPO_DOC": "",
            "NRO_DOC": "",
        }

        tipo, confidence, metadata = self.detector.detectar(row)

        assert tipo == "animal"
        assert confidence >= 0.5
        assert "subespecie" in metadata

    def test_caso_indeterminado_datos_contradictorios(self):
        """Test caso ambiguo que requiere revisión."""
        row = {
            "NOMBRE": "CARLOS",  # Nombre de persona
            "APELLIDO": "RODRIGUEZ",  # Apellido de persona
            "SEXO": "IND",  # Sexo indeterminado (típico de animal)
            "TIPO_DOC": "",  # Sin documento
            "NRO_DOC": "",
        }

        tipo, confidence, metadata = self.detector.detectar(row)

        assert tipo == "indeterminado"
        assert "razon_ambiguedad" in metadata
        assert (
            "Sexo indeterminado pero tiene nombre específico"
            in metadata["razon_ambiguedad"]
        )

    def test_caso_indeterminado_documento_no_estandar(self):
        """Test caso con documento no estándar."""
        row = {
            "NOMBRE": "ROBERTO",
            "APELLIDO": "SILVA",
            "SEXO": "M",
            "TIPO_DOC": "OTRO",  # Tipo no estándar
            "NRO_DOC": "12345",
        }

        tipo, confidence, metadata = self.detector.detectar(row)

        # Podría ser humano o indeterminado dependiendo de los pesos
        assert tipo in ["humano", "indeterminado"]
        if tipo == "indeterminado":
            assert "razon_ambiguedad" in metadata

    def test_humano_caso_real_santino(self):
        """Test con caso real del CSV: SANTINO GAEL MELLADO."""
        row = {
            "NOMBRE": "SANTINO GAEL",
            "APELLIDO": "MELLADO",
            "SEXO": "M",
            "TIPO_DOC": "DNI",
            "NRO_DOC": "45123456",
        }

        tipo, confidence, metadata = self.detector.detectar(row)

        assert tipo == "humano"
        assert confidence >= 0.7
        assert metadata["nombre_completo"] == "SANTINO GAEL MELLADO"

    def test_animal_caso_no_hematofago(self):
        """Test con término técnico específico NO HEMATOFAGO."""
        row = {
            "NOMBRE": "MURCIELAGO",
            "APELLIDO": "NO HEMATOFAGO",
            "SEXO": "IND",
            "TIPO_DOC": "",
            "NRO_DOC": "",
        }

        tipo, confidence, metadata = self.detector.detectar(row)

        assert tipo == "animal"
        assert confidence >= 0.5
        assert metadata["especie"] == "MURCIELAGO"
        assert "NO HEMATOFAGO" in metadata["subespecie"]

    def test_confidence_scores_coherentes(self):
        """Test que los scores de confidence sean coherentes."""
        # Caso muy claro de humano
        humano_claro = {
            "NOMBRE": "ANA",
            "APELLIDO": "MARTINEZ",
            "SEXO": "F",
            "TIPO_DOC": "DNI",
            "NRO_DOC": "12345678",
        }

        # Caso muy claro de animal
        animal_claro = {
            "NOMBRE": "NN",
            "APELLIDO": "TADARIDA BRASILIENSIS",
            "SEXO": "IND",
            "TIPO_DOC": "",
            "NRO_DOC": "",
        }

        tipo_h, conf_h, _ = self.detector.detectar(humano_claro)
        tipo_a, conf_a, _ = self.detector.detectar(animal_claro)

        assert tipo_h == "humano"
        assert tipo_a == "animal"
        assert conf_h >= 0.7  # Alta confianza para humano claro
        assert conf_a >= 0.5  # Confianza razonable para animal claro


class TestMetadataExtractor:
    """Tests para el extractor de metadata adicional."""

    def setup_method(self):
        """Setup para cada test."""
        self.extractor = MetadataExtractor()

    def test_extrae_fuente_contagio_murcielago(self):
        """Test extracción de fuente de contagio: murciélago."""
        row = {"NOMBRE": "TADARIDA", "APELLIDO": "BRASILIENSIS"}

        fuente = self.extractor.extraer_fuente_contagio(row)

        assert fuente == "murcielago"  # Normalizado

    def test_extrae_fuente_contagio_zorro(self):
        """Test extracción de fuente de contagio: zorro."""
        row = {"NOMBRE": "ZORRO", "APELLIDO": "GRIS"}

        fuente = self.extractor.extraer_fuente_contagio(row)

        assert fuente == "zorro"

    def test_extrae_fuente_contagio_perro(self):
        """Test extracción de fuente de contagio: perro."""
        row = {"NOMBRE": "PERRO", "APELLIDO": "CALLEJERO"}

        fuente = self.extractor.extraer_fuente_contagio(row)

        assert fuente == "perro"

    def test_normaliza_muercielago_a_murcielago(self):
        """Test normalización de 'muercielago' a 'murcielago'."""
        row = {"NOMBRE": "MUERCIELAGO", "APELLIDO": "VAMPIRO"}

        fuente = self.extractor.extraer_fuente_contagio(row)

        assert fuente == "murcielago"  # Normalizado

    def test_normaliza_especies_cientificas_a_murcielago(self):
        """Test normalización de especies científicas a 'murcielago'."""
        test_cases = [
            ({"NOMBRE": "MYOTIS", "APELLIDO": "CHILOENSIS"}, "murcielago"),
            ({"NOMBRE": "LASIURUS", "APELLIDO": "BOREALIS"}, "murcielago"),
            ({"NOMBRE": "HISTIOTUS", "APELLIDO": "MONTANUS"}, "murcielago"),
        ]

        for row, expected in test_cases:
            fuente = self.extractor.extraer_fuente_contagio(row)
            assert fuente == expected

    def test_no_encuentra_fuente_contagio(self):
        """Test cuando no se encuentra fuente de contagio."""
        row = {"NOMBRE": "JUAN", "APELLIDO": "PEREZ"}

        fuente = self.extractor.extraer_fuente_contagio(row)

        assert fuente is None

    def test_busca_en_nombre_y_apellido(self):
        """Test que busca tanto en nombre como apellido."""
        row_nombre = {"NOMBRE": "GATO", "APELLIDO": "DOMESTICO"}

        row_apellido = {"NOMBRE": "ANIMAL", "APELLIDO": "ZORRO"}

        fuente_nombre = self.extractor.extraer_fuente_contagio(row_nombre)
        fuente_apellido = self.extractor.extraer_fuente_contagio(row_apellido)

        assert fuente_nombre == "gato"
        assert fuente_apellido == "zorro"

    def test_case_insensitive(self):
        """Test que la búsqueda es insensitive al case."""
        row = {"NOMBRE": "muRciELaGo", "APELLIDO": "GRANDE"}

        fuente = self.extractor.extraer_fuente_contagio(row)

        assert fuente == "murcielago"


if __name__ == "__main__":
    pytest.main([__file__])

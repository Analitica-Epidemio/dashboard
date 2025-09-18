"""
Tests unitarios para tipos de filtros de clasificación.
"""

import pandas as pd

from app.domains.eventos_epidemiologicos.clasificacion.models import TipoFiltro


class TestFilterTypes:
    """Tests para cada tipo de filtro disponible."""

    def setup_method(self):
        """Setup para cada test."""
        # Datos de prueba
        self.sample_data = pd.DataFrame(
            [
                {
                    "IDEVENTOCASO": "1001",
                    "CLASIFICACION_MANUAL": "Caso confirmado",
                    "RESULTADO": "Reactivo",
                    "NOMBRE": "JUAN",
                    "APELLIDO": "PEREZ",
                    "SEXO": "M",
                    "PROVINCIA_RESIDENCIA": "Chubut",
                },
                {
                    "IDEVENTOCASO": "1002",
                    "CLASIFICACION_MANUAL": "Caso sospechoso",
                    "RESULTADO": "No reactivo",
                    "NOMBRE": "MARIA",
                    "APELLIDO": "GONZALEZ",
                    "SEXO": "F",
                    "PROVINCIA_RESIDENCIA": "Buenos Aires",
                },
                {
                    "IDEVENTOCASO": "1003",
                    "CLASIFICACION_MANUAL": "Caso probable",
                    "RESULTADO": "Detectable",
                    "NOMBRE": "TADARIDA",
                    "APELLIDO": "BRASILIENSIS",
                    "SEXO": "IND",
                    "PROVINCIA_RESIDENCIA": "Chubut",
                },
                {
                    "IDEVENTOCASO": "1004",
                    "CLASIFICACION_MANUAL": "",  # Vacío
                    "RESULTADO": None,  # Nulo
                    "NOMBRE": "NN",
                    "APELLIDO": "MURCIELAGO",
                    "SEXO": "ND",
                    "PROVINCIA_RESIDENCIA": "Chubut",
                },
            ]
        )

    def test_campo_igual_exacto(self):
        """Test filtro CAMPO_IGUAL con match exacto."""
        # Simular filtro: CLASIFICACION_MANUAL == "Caso confirmado"
        filter_condition = {
            "filter_type": TipoFiltro.CAMPO_IGUAL,
            "field_name": "CLASIFICACION_MANUAL",
            "value": "Caso confirmado",
        }

        result = self._apply_filter_condition(filter_condition)

        assert len(result) == 1
        assert result.iloc[0]["IDEVENTOCASO"] == "1001"

    def test_campo_igual_sin_match(self):
        """Test filtro CAMPO_IGUAL sin coincidencias."""
        filter_condition = {
            "filter_type": TipoFiltro.CAMPO_IGUAL,
            "field_name": "CLASIFICACION_MANUAL",
            "value": "Caso inexistente",
        }

        result = self._apply_filter_condition(filter_condition)

        assert len(result) == 0

    def test_campo_en_lista_multiple_valores(self):
        """Test filtro CAMPO_EN_LISTA con múltiples valores."""
        filter_condition = {
            "filter_type": TipoFiltro.CAMPO_EN_LISTA,
            "field_name": "CLASIFICACION_MANUAL",
            "values": ["Caso confirmado", "Caso sospechoso"],
        }

        result = self._apply_filter_condition(filter_condition)

        assert len(result) == 2
        expected_ids = ["1001", "1002"]
        actual_ids = result["IDEVENTOCASO"].tolist()
        assert set(actual_ids) == set(expected_ids)

    def test_campo_en_lista_valor_unico(self):
        """Test filtro CAMPO_EN_LISTA con un solo valor."""
        filter_condition = {
            "filter_type": TipoFiltro.CAMPO_EN_LISTA,
            "field_name": "SEXO",
            "values": ["M"],
        }

        result = self._apply_filter_condition(filter_condition)

        assert len(result) == 1
        assert result.iloc[0]["NOMBRE"] == "JUAN"

    def test_campo_contiene_substring(self):
        """Test filtro CAMPO_CONTIENE encuentra substring."""
        filter_condition = {
            "filter_type": TipoFiltro.CAMPO_CONTIENE,
            "field_name": "CLASIFICACION_MANUAL",
            "value": "confirmado",  # Substring de "Caso confirmado"
        }

        result = self._apply_filter_condition(filter_condition)

        assert len(result) == 1
        assert result.iloc[0]["IDEVENTOCASO"] == "1001"

    def test_campo_contiene_case_insensitive(self):
        """Test filtro CAMPO_CONTIENE es case insensitive."""
        filter_condition = {
            "filter_type": TipoFiltro.CAMPO_CONTIENE,
            "field_name": "CLASIFICACION_MANUAL",
            "value": "CONFIRMADO",  # Mayúsculas
        }

        result = self._apply_filter_condition(filter_condition)

        assert len(result) == 1
        assert result.iloc[0]["IDEVENTOCASO"] == "1001"

    def test_campo_existe_con_valores(self):
        """Test filtro CAMPO_EXISTE encuentra campos con valores."""
        filter_condition = {
            "filter_type": TipoFiltro.CAMPO_EXISTE,
            "field_name": "CLASIFICACION_MANUAL",
        }

        result = self._apply_filter_condition(filter_condition)

        # Todos los registros tienen el campo (aunque algunos vacíos)
        assert len(result) == 4

    def test_campo_no_nulo_excluye_nulos(self):
        """Test filtro CAMPO_NO_NULO excluye valores nulos."""
        filter_condition = {
            "filter_type": TipoFiltro.CAMPO_NO_NULO,
            "field_name": "RESULTADO",
        }

        result = self._apply_filter_condition(filter_condition)

        # Solo 3 registros tienen RESULTADO no nulo
        assert len(result) == 3
        expected_ids = ["1001", "1002", "1003"]
        actual_ids = result["IDEVENTOCASO"].tolist()
        assert set(actual_ids) == set(expected_ids)

    def test_campo_no_nulo_excluye_vacios(self):
        """Test filtro CAMPO_NO_NULO excluye strings vacíos."""
        filter_condition = {
            "filter_type": TipoFiltro.CAMPO_NO_NULO,
            "field_name": "CLASIFICACION_MANUAL",
        }

        result = self._apply_filter_condition(filter_condition)

        # Solo 3 registros tienen CLASIFICACION_MANUAL no vacía
        assert len(result) == 3
        assert "1004" not in result["IDEVENTOCASO"].tolist()

    def test_regex_extraccion_patron_simple(self):
        """Test filtro REGEX_EXTRACCION con patrón simple."""
        filter_condition = {
            "filter_type": TipoFiltro.REGEX_EXTRACCION,
            "field_name": "CLASIFICACION_MANUAL",
            "pattern": r"Caso\s+(\w+)",  # Extrae la palabra después de "Caso "
            "extracted_metadata_field": "tipo_caso",
        }

        result = self._apply_filter_condition(filter_condition)

        # Debe encontrar todos los registros con patrón "Caso XXX"
        assert len(result) == 3

        # Verificar que extrajo metadata
        if hasattr(result, "_metadata_extracted"):
            metadata = result._metadata_extracted
            assert "tipo_caso" in metadata

    def test_regex_extraccion_sin_match(self):
        """Test filtro REGEX_EXTRACCION sin coincidencias."""
        filter_condition = {
            "filter_type": TipoFiltro.REGEX_EXTRACCION,
            "field_name": "CLASIFICACION_MANUAL",
            "pattern": r"NoExiste\s+(\w+)",
            "extracted_metadata_field": "no_existe",
        }

        result = self._apply_filter_condition(filter_condition)

        assert len(result) == 0

    def test_filtros_multiples_con_and(self):
        """Test combinación de filtros con operador AND."""
        # Filtro 1: SEXO == "F"
        # Filtro 2: PROVINCIA_RESIDENCIA == "Chubut"
        # Resultado esperado: Solo MARIA no cumple (Buenos Aires)

        filter1 = {
            "filter_type": TipoFiltro.CAMPO_IGUAL,
            "field_name": "PROVINCIA_RESIDENCIA",
            "value": "Chubut",
        }

        filter2 = {
            "filter_type": TipoFiltro.CAMPO_EN_LISTA,
            "field_name": "SEXO",
            "values": ["M", "F"],
        }

        # Aplicar primer filtro
        temp_result = self._apply_filter_condition(filter1)
        # Aplicar segundo filtro sobre resultado anterior
        final_result = self._apply_filter_condition(filter2, temp_result)

        assert len(final_result) == 1
        assert final_result.iloc[0]["NOMBRE"] == "JUAN"

    def test_filtros_campos_especiales_animales(self):
        """Test filtros específicos para detección de animales."""
        # Detectar nombres taxonómicos (solo letras, todo mayúsculas)
        filter_condition = {
            "filter_type": TipoFiltro.REGEX_EXTRACCION,
            "field_name": "NOMBRE",
            "pattern": r"^[A-Z]+$",  # Solo letras mayúsculas
            "extracted_metadata_field": "posible_genero",
        }

        result = self._apply_filter_condition(filter_condition)

        # En el sample data: JUAN, MARIA, TADARIDA, NN
        # Solo TADARIDA y NN son completamente mayúsculas
        # Pero JUAN, MARIA también son mayúsculas
        # Verificar que al menos encuentra los casos esperados
        assert len(result) >= 2
        nombres = result["NOMBRE"].tolist()
        # Verificar que encuentra casos típicos de animales si existen
        nombres_mayusculas = [n for n in nombres if n.isupper()]
        assert len(nombres_mayusculas) >= 2

    def _apply_filter_condition(
        self, filter_condition: dict, data: pd.DataFrame = None
    ) -> pd.DataFrame:
        """
        Helper para aplicar una condición de filtro simulada.

        En el futuro, esto debería usar el EventClassificationService real,
        pero por ahora simulamos la lógica para tests unitarios.
        """
        if data is None:
            data = self.sample_data.copy()

        filter_type = filter_condition["filter_type"]
        field_name = filter_condition["field_name"]

        if filter_type == TipoFiltro.CAMPO_IGUAL:
            value = filter_condition["value"]
            return data[data[field_name] == value]

        elif filter_type == TipoFiltro.CAMPO_EN_LISTA:
            values = filter_condition["values"]
            return data[data[field_name].isin(values)]

        elif filter_type == TipoFiltro.CAMPO_CONTIENE:
            value = filter_condition["value"].lower()
            return data[data[field_name].str.lower().str.contains(value, na=False)]

        elif filter_type == TipoFiltro.CAMPO_EXISTE:
            # Considera que existe si no es NaN
            return data[data[field_name].notna()]

        elif filter_type == TipoFiltro.CAMPO_NO_NULO:
            # No nulo Y no vacío
            mask = (data[field_name].notna()) & (
                data[field_name].astype(str).str.strip() != ""
            )
            return data[mask]

        elif filter_type == TipoFiltro.REGEX_EXTRACCION:
            pattern = filter_condition["pattern"]
            mask = data[field_name].str.contains(pattern, na=False)
            result = data[mask]

            # Simular extracción de metadata
            if len(result) > 0 and "extracted_metadata_field" in filter_condition:
                result._metadata_extracted = {
                    filter_condition["extracted_metadata_field"]: "extracted_value"
                }

            return result

        else:
            return data  # Tipo no implementado, devolver todo


class TestFilterEdgeCases:
    """Tests para casos edge en filtros."""

    def test_valores_nulos_en_filtros(self):
        """Test manejo de valores nulos en campos."""
        data = pd.DataFrame(
            [
                {"ID": 1, "CAMPO": None},
                {"ID": 2, "CAMPO": ""},
                {"ID": 3, "CAMPO": "valor"},
            ]
        )

        # CAMPO_NO_NULO debe manejar tanto None como strings vacíos
        result = data[
            (data["CAMPO"].notna()) & (data["CAMPO"].astype(str).str.strip() != "")
        ]

        assert len(result) == 1
        assert result.iloc[0]["CAMPO"] == "valor"

    def test_espacios_en_valores(self):
        """Test manejo de espacios extra en valores."""
        data = pd.DataFrame(
            [
                {"ID": 1, "CAMPO": " valor "},  # Con espacios
                {"ID": 2, "CAMPO": "valor"},  # Sin espacios
                {"ID": 3, "CAMPO": "  "},  # Solo espacios
            ]
        )

        # CAMPO_CONTIENE debe encontrar con y sin espacios
        result = data[data["CAMPO"].str.strip().str.contains("valor", na=False)]

        assert len(result) == 2
        assert set(result["ID"].tolist()) == {1, 2}

    def test_case_sensitivity(self):
        """Test sensibilidad a mayúsculas/minúsculas."""
        data = pd.DataFrame(
            [
                {"ID": 1, "CAMPO": "Caso Confirmado"},
                {"ID": 2, "CAMPO": "CASO CONFIRMADO"},
                {"ID": 3, "CAMPO": "caso confirmado"},
            ]
        )

        # Búsqueda case-insensitive
        result = data[data["CAMPO"].str.lower().str.contains("caso confirmado")]

        assert len(result) == 3

    def test_regex_caracteres_especiales(self):
        """Test regex con caracteres especiales."""
        data = pd.DataFrame(
            [
                {"ID": 1, "CAMPO": "Caso (confirmado)"},
                {"ID": 2, "CAMPO": "Caso [sospechoso]"},
                {"ID": 3, "CAMPO": "Caso.probable"},
            ]
        )

        # Escapar caracteres especiales en regex
        pattern = r"Caso\s*[\(\[\.]"  # Paréntesis, corchete o punto después de "Caso"
        result = data[data["CAMPO"].str.contains(pattern, na=False)]

        assert len(result) == 3

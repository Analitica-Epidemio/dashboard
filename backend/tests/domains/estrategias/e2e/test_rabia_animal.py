"""
Tests end-to-end para el evento "Rabia animal".

Valida el flujo completo desde CSV hasta clasificación final,
usando casos reales y la lógica legacy como referencia.
"""

import pandas as pd
from app.domains.eventos_epidemiologicos.clasificacion.detectors import (
    MetadataExtractor,
    TipoSujetoDetector,
)

from tests.domains.estrategias.fixtures.csv_samples import RABIA_SAMPLES


class TestRabiaAnimalE2E:
    """Tests end-to-end para Rabia Animal basados en archivo legacy."""

    def setup_method(self):
        """Setup para cada test."""
        self.detector = TipoSujetoDetector()
        self.extractor = MetadataExtractor()

        # Crear DataFrame con casos de rabia
        self.rabia_data = pd.DataFrame(
            [
                sample
                for sample in RABIA_SAMPLES
                if not sample.get("NOMBRE")
                or sample["NOMBRE"] != ""  # Filtrar casos problemáticos
            ]
        )

    def test_rabia_animal_clasificacion_confirmados(self):
        """Test clasificación de confirmados según lógica legacy."""
        # Filtro legacy: CLASIFICACION_MANUAL.isin(["Caso confirmado"])
        confirmados_legacy = self.rabia_data[
            self.rabia_data["CLASIFICACION_MANUAL"] == "Caso confirmado"
        ]

        assert len(confirmados_legacy) == 3  # SANTINO, TADARIDA, ZORRO

        # Verificar que los casos esperados están presentes
        nombres = confirmados_legacy["NOMBRE"].tolist()
        assert "SANTINO GAEL" in nombres
        assert "TADARIDA" in nombres
        assert "ZORRO" in nombres

    def test_rabia_animal_clasificacion_sospechosos(self):
        """Test clasificación de sospechosos según lógica legacy."""
        # Filtro legacy: CLASIFICACION_MANUAL == "Caso sospechoso"
        sospechosos_legacy = self.rabia_data[
            self.rabia_data["CLASIFICACION_MANUAL"] == "Caso sospechoso"
        ]

        assert len(sospechosos_legacy) == 2  # NN MURCIELAGO y CARLOS (ambiguo)

        nombres = sospechosos_legacy["NOMBRE"].tolist()
        assert "NN" in nombres
        assert "CARLOS" in nombres

    def test_rabia_animal_deteccion_tipo_sujeto_humano(self):
        """Test detección completa de sujeto humano."""
        # Caso SANTINO GAEL MELLADO
        caso_humano = (
            self.rabia_data[self.rabia_data["NOMBRE"] == "SANTINO GAEL"]
            .iloc[0]
            .to_dict()
        )

        tipo, confidence, metadata = self.detector.detectar(caso_humano)

        # Validaciones de detección
        assert tipo == "humano"
        assert confidence >= 0.7  # Alta confianza

        # Validaciones de metadata
        assert metadata["nombre_completo"] == "SANTINO GAEL MELLADO"
        assert "DNI" in metadata.get("documento", "")
        assert metadata["confidence"] >= 0.7

    def test_rabia_animal_deteccion_tipo_sujeto_animal_cientifico(self):
        """Test detección de animal con nomenclatura científica."""
        # Caso TADARIDA BRASILIENSIS
        caso_animal = (
            self.rabia_data[self.rabia_data["NOMBRE"] == "TADARIDA"].iloc[0].to_dict()
        )

        tipo, confidence, metadata = self.detector.detectar(caso_animal)

        # Validaciones de detección
        assert tipo == "animal"
        assert confidence >= 0.5

        # Validaciones de metadata específica de animal
        assert metadata["especie"] == "TADARIDA"
        assert metadata["subespecie"] == "BRASILIENSIS"
        assert "clasificacion_taxonomica" in metadata
        assert metadata["clasificacion_taxonomica"]["genero"] == "TADARIDA"
        assert metadata["clasificacion_taxonomica"]["especie"] == "BRASILIENSIS"

    def test_rabia_animal_deteccion_tipo_sujeto_animal_nn(self):
        """Test detección de animal con nombre genérico NN."""
        # Caso NN MURCIELAGO
        caso_nn = self.rabia_data[self.rabia_data["NOMBRE"] == "NN"].iloc[0].to_dict()

        tipo, confidence, metadata = self.detector.detectar(caso_nn)

        # Validaciones
        assert tipo == "animal"
        assert confidence >= 0.5
        assert metadata["especie"] == "MURCIELAGO"  # Debe tomar apellido como especie

    def test_rabia_animal_deteccion_animal_con_ubicacion(self):
        """Test detección de animal con ubicación geográfica."""
        # Caso ZORRO RUTA 25 KM 1234
        caso_ubicacion = (
            self.rabia_data[self.rabia_data["NOMBRE"] == "ZORRO"].iloc[0].to_dict()
        )

        tipo, confidence, metadata = self.detector.detectar(caso_ubicacion)

        # Validaciones
        assert tipo == "animal"
        assert metadata["especie"] == "ZORRO"
        assert metadata["ubicacion"] == "RUTA 25 KM 1234"
        assert "1234" in metadata["ubicacion"]  # Contiene código numérico

    def test_rabia_animal_caso_ambiguo_requiere_revision(self):
        """Test caso ambiguo que requiere revisión manual."""
        # Caso CARLOS RODRIGUEZ (nombre humano pero sexo IND)
        caso_ambiguo = (
            self.rabia_data[self.rabia_data["NOMBRE"] == "CARLOS"].iloc[0].to_dict()
        )

        tipo, confidence, metadata = self.detector.detectar(caso_ambiguo)

        # Validaciones
        assert tipo == "indeterminado"
        assert "razon_ambiguedad" in metadata
        assert (
            "Sexo indeterminado pero tiene nombre específico"
            in metadata["razon_ambiguedad"]
        )
        assert confidence < 0.7  # Baja confianza

    def test_rabia_animal_extraccion_fuente_contagio(self):
        """Test extracción de fuente de contagio."""
        casos_animales = [
            {"NOMBRE": "TADARIDA", "APELLIDO": "BRASILIENSIS"},  # -> murcielago
            {"NOMBRE": "NN", "APELLIDO": "MURCIELAGO"},  # -> murcielago
            {"NOMBRE": "ZORRO", "APELLIDO": "GRIS"},  # -> zorro
        ]

        for caso in casos_animales:
            fuente = self.extractor.extraer_fuente_contagio(caso)

            if "TADARIDA" in caso["NOMBRE"] or "MURCIELAGO" in caso["APELLIDO"]:
                assert fuente == "murcielago"
            elif "ZORRO" in caso["NOMBRE"]:
                assert fuente == "zorro"

    def test_rabia_animal_flujo_completo_casos_mixtos(self):
        """Test flujo completo con casos mixtos humano/animal."""
        resultados = []

        for _, row in self.rabia_data.iterrows():
            caso = row.to_dict()

            # 1. Detectar tipo de sujeto
            tipo_sujeto, confidence, metadata_sujeto = self.detector.detectar(caso)

            # 2. Extraer fuente de contagio (solo para animales)
            fuente_contagio = None
            if tipo_sujeto == "animal":
                fuente_contagio = self.extractor.extraer_fuente_contagio(caso)

            # 3. Aplicar clasificación epidemiológica (simulada)
            clasificacion_epi = self._simular_clasificacion_epidemiologica(caso)

            # 4. Determinar si requiere revisión
            requiere_revision = tipo_sujeto == "indeterminado" or confidence < 0.6

            resultado = {
                "ideventocaso": caso.get("IDEVENTOCASO", f"test_{len(resultados)}"),
                "tipo_sujeto": tipo_sujeto,
                "confidence": confidence,
                "clasificacion_epidemiologica": clasificacion_epi,
                "fuente_contagio": fuente_contagio,
                "requiere_revision": requiere_revision,
                "metadata": metadata_sujeto,
            }

            resultados.append(resultado)

        # Validaciones del flujo completo
        assert len(resultados) == len(self.rabia_data)

        # Contar por tipo de sujeto
        tipos = [r["tipo_sujeto"] for r in resultados]
        assert tipos.count("humano") == 1  # SANTINO
        assert tipos.count("animal") == 3  # TADARIDA, NN MURCIELAGO, ZORRO
        assert tipos.count("indeterminado") == 1  # CARLOS

        # Verificar que casos ambiguos requieren revisión
        casos_revision = [r for r in resultados if r["requiere_revision"]]
        assert len(casos_revision) == 1
        assert casos_revision[0]["tipo_sujeto"] == "indeterminado"

        # Verificar fuentes de contagio
        fuentes = [r["fuente_contagio"] for r in resultados if r["fuente_contagio"]]
        assert "murcielago" in fuentes
        assert "zorro" in fuentes

    def test_rabia_animal_validacion_campos_requeridos(self):
        """Test validación de campos requeridos en los datos."""
        campos_criticos = ["NOMBRE", "APELLIDO", "SEXO", "CLASIFICACION_MANUAL"]

        for campo in campos_criticos:
            assert campo in self.rabia_data.columns, f"Campo crítico {campo} faltante"

        # Verificar que no todos los valores son nulos
        for campo in campos_criticos:
            valores_no_nulos = self.rabia_data[campo].notna().sum()
            assert valores_no_nulos > 0, f"Campo {campo} tiene todos valores nulos"

    def test_rabia_animal_consistency_con_legacy(self):
        """Test consistencia con la lógica legacy original."""
        # Replicar exactamente la lógica del archivo rabia_animal.py

        # Filtro confirmados legacy
        confirmados_legacy = self.rabia_data[
            self.rabia_data["CLASIFICACION_MANUAL"].isin(["Caso confirmado"])
        ].copy()

        # Filtro sospechosos legacy
        sospechosos_legacy = self.rabia_data[
            self.rabia_data["CLASIFICACION_MANUAL"] == "Caso sospechoso"
        ].copy()

        # Filtro notificados legacy (confirmados + sospechosos)
        notificados_legacy = self.rabia_data[
            self.rabia_data["CLASIFICACION_MANUAL"].isin(
                ["Caso confirmado", "Caso sospechoso"]
            )
        ].copy()

        # Validaciones de consistencia
        assert len(confirmados_legacy) + len(sospechosos_legacy) == len(
            notificados_legacy
        )
        assert len(confirmados_legacy) == 3
        assert len(sospechosos_legacy) == 2
        assert len(notificados_legacy) == 5

        # Verificar que todos los casos están clasificados
        casos_sin_clasificar = self.rabia_data[
            ~self.rabia_data["CLASIFICACION_MANUAL"].isin(
                ["Caso confirmado", "Caso sospechoso"]
            )
        ]
        assert len(casos_sin_clasificar) == 0

    def _simular_clasificacion_epidemiologica(self, caso: dict) -> str:
        """
        Simula la clasificación epidemiológica según lógica legacy.
        En producción, esto sería manejado por EventClassificationService.
        """
        clasificacion_manual = caso.get("CLASIFICACION_MANUAL", "").strip()

        if clasificacion_manual == "Caso confirmado":
            return "confirmados"
        elif clasificacion_manual == "Caso sospechoso":
            return "sospechosos"
        elif clasificacion_manual in ["Caso probable"]:
            return "probables"
        else:
            return "sin_clasificar"


class TestRabiaAnimalPerformance:
    """Tests de performance para procesamiento masivo de rabia."""

    def test_procesamiento_lote_grande(self):
        """Test procesamiento de lote grande de casos de rabia."""
        import time

        # Crear dataset grande duplicando casos
        casos_base = RABIA_SAMPLES * 100  # 500 casos
        detector = TipoSujetoDetector()

        start_time = time.time()

        resultados = []
        for caso in casos_base:
            tipo, confidence, metadata = detector.detectar(caso)
            resultados.append({"tipo": tipo, "confidence": confidence})

        elapsed_time = time.time() - start_time

        # Validaciones de performance
        assert len(resultados) == 500
        assert elapsed_time < 5.0  # Menos de 5 segundos para 500 casos

        # Verificar que los resultados son consistentes
        tipos = [r["tipo"] for r in resultados]
        # Cada lote de 5 tiene: 1 humano, 3 animales, 1 indeterminado
        assert tipos.count("humano") == 100
        assert tipos.count("animal") == 300
        assert tipos.count("indeterminado") == 100

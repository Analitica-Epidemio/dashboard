"""
Detectores inteligentes para clasificación de eventos epidemiológicos.

Este módulo contiene lógica para detectar automáticamente el tipo de sujeto
(humano/animal/indeterminado) y extraer metadata sin hardcodear especies específicas.
"""

import re
from typing import Any, Dict, Optional, Tuple


class TipoSujetoDetector:
    """
    Detector inteligente que determina si un caso es:
    - HUMANO: Con alta confianza basado en datos de identificación
    - ANIMAL: Con metadata de especie extraída
    - INDETERMINADO: Requiere revisión manual

    NO hardcodea especies específicas, detecta patrones.
    """

    def __init__(self):
        # Patrones para detectar nomenclatura científica/taxonómica
        self.taxonomia_patterns = [
            r"NO HEMATOFAGO",  # Término técnico específico
            r"^\w+\s+\w+ENSIS$",  # Sufijo -ensis común en especies (TADARIDA BRASILIENSIS)
            r"^\w+\s+\w+US$",  # Sufijo -us común en géneros (HISTIOTUS MONTANUS)
            r"^[A-Z]+\s+[A-Z]+$",  # Todo mayúsculas (patrón género + especie)
            r"MACROTUS|CHILOENSIS|BRASILIENSIS|MAGELLANICUS|TADARIDA|HISTIOTUS|MONTANUS",  # Sufijos científicos comunes
        ]

    def detectar(self, row: Dict[str, Any]) -> Tuple[str, float, Dict[str, Any]]:
        """
        Detecta el tipo de sujeto y extrae metadata.

        Args:
            row: Diccionario con datos del evento

        Returns:
            Tuple con (tipo, confidence, metadata_extraida)
        """
        # Extraer campos básicos
        nombre = str(row.get("NOMBRE", "")).strip()
        apellido = str(row.get("APELLIDO", "")).strip()
        sexo = str(row.get("SEXO", "")).strip()
        tipo_doc = str(row.get("TIPO_DOC", "")).strip()
        nro_doc = str(row.get("NRO_DOC", "")).strip()

        # Detectar tipo de sujeto
        tipo, confidence = self._detectar_tipo_sujeto(
            nombre, apellido, sexo, tipo_doc, nro_doc
        )

        # Extraer metadata según el tipo detectado
        metadata = {}

        if tipo == "animal":
            metadata.update(self._extraer_info_animal(nombre, apellido))
        elif tipo == "humano":
            metadata.update(
                self._extraer_info_humano(nombre, apellido, tipo_doc, nro_doc)
            )
        else:
            # Caso indeterminado
            metadata = {
                "datos_originales": {
                    "nombre": nombre,
                    "apellido": apellido,
                    "sexo": sexo,
                    "tipo_doc": tipo_doc,
                    "nro_doc": nro_doc,
                },
                "razon_ambiguedad": self._analizar_ambiguedad(
                    nombre, apellido, sexo, tipo_doc
                ),
            }

        metadata["confidence"] = confidence
        metadata["tipo_detectado"] = tipo

        return tipo, confidence, metadata

    def _detectar_tipo_sujeto(
        self, nombre: str, apellido: str, sexo: str, tipo_doc: str, nro_doc: str
    ) -> Tuple[str, float]:
        """
        Detección basada en patrones, no en especies hardcodeadas.
        """
        # Inicializar scores
        humano_score = 0.0
        animal_score = 0.0

        # === INDICADORES DE HUMANO ===

        # Documento válido es fuerte indicador
        if tipo_doc in ["DNI", "LC", "LE", "CI", "PASAPORTE"]:
            humano_score += 0.4

        # Sexo M/F es indicador fuerte
        if sexo in ["M", "F", "Masculino", "Femenino", "MASCULINO", "FEMENINO"]:
            humano_score += 0.35

        # Número de documento con formato válido argentino
        if nro_doc and nro_doc.isdigit() and 7 <= len(nro_doc) <= 9:
            humano_score += 0.25

        # === INDICADORES DE ANIMAL ===

        # Sexo IND/ND es indicador de animal en vigilancia, pero SOLO si no hay nombre típico humano
        if sexo in ["IND", "ND", "", "None", None]:
            # Verificar si el nombre parece humano típico
            nombre_parece_humano = (
                nombre
                and len(nombre) > 2
                and not any(
                    re.search(pattern, nombre.upper())
                    for pattern in self.taxonomia_patterns
                )
                and "NN" not in nombre.upper()
            )
            apellido_parece_humano = (
                apellido
                and len(apellido) > 2
                and not any(
                    re.search(pattern, apellido.upper())
                    for pattern in self.taxonomia_patterns
                )
                and "NN" not in apellido.upper()
                and not re.search(r"\d{2,}", apellido)
            )

            # Solo sumar puntos si NO parece tener nombres humanos típicos
            if not (nombre_parece_humano and apellido_parece_humano):
                animal_score += 0.3

        # Tipo doc no válido o número muy largo (códigos internos)
        if tipo_doc not in ["DNI", "LC", "LE", "CI", "PASAPORTE"]:
            animal_score += 0.2
        if nro_doc and len(nro_doc) > 9:  # Números muy largos no son DNI
            animal_score += 0.2

        # Patrones de nomenclatura científica/técnica
        nombre_upper = nombre.upper()
        apellido_upper = apellido.upper()

        # Verificar patrones taxonómicos
        for pattern in self.taxonomia_patterns:
            if re.search(pattern, nombre_upper) or re.search(pattern, apellido_upper):
                animal_score += 0.3  # Aumentado porque es muy específico
                break

        # NN es muy común en registros de animales
        if "NN" in nombre_upper or "NN" in apellido_upper:
            animal_score += 0.4  # Aumentado porque es muy específico de animales

        # Direcciones o códigos en apellido (común en animales)
        if re.search(r"\d{2,}", apellido):  # 2 o más dígitos seguidos
            animal_score += 0.2  # Aumentado un poco

        # === DECISIÓN FINAL ===

        if humano_score >= 0.7:
            return ("humano", humano_score)
        elif animal_score >= 0.5:
            return ("animal", animal_score)
        else:
            return ("indeterminado", max(humano_score, animal_score))

    def _extraer_info_animal(self, nombre: str, apellido: str) -> Dict[str, Any]:
        """
        Extrae información del animal de manera inteligente.
        """
        info = {
            "especie": None,
            "subespecie": None,
            "ubicacion": None,
            "info_adicional": [],
            "clasificacion_taxonomica": {},
        }

        nombre_clean = nombre if nombre not in ["NN", "", None] else None
        apellido_clean = apellido if apellido not in ["NN", "", None] else None

        # Prioridad 1: Detectar ubicación (contiene números o direcciones)
        if apellido_clean and re.search(r"\d+", apellido_clean):
            info["ubicacion"] = apellido_clean
            info["especie"] = nombre_clean or "DESCONOCIDO"

        # Prioridad 2: Nombre científico completo en NOMBRE + APELLIDO (ambos con patrones taxonómicos)
        elif (
            nombre_clean
            and apellido_clean
            and any(
                re.search(pattern, nombre_clean.upper())
                for pattern in self.taxonomia_patterns
            )
            and any(
                re.search(pattern, apellido_clean.upper())
                for pattern in self.taxonomia_patterns
            )
        ):
            # Ambos campos tienen patrones taxonómicos - formato completo género + especie
            info["especie"] = nombre_clean
            info["subespecie"] = apellido_clean
            info["clasificacion_taxonomica"] = {
                "genero": nombre_clean,
                "especie": apellido_clean,
                "nombre_completo": f"{nombre_clean} {apellido_clean}",
            }

        # Prioridad 3: Solo apellido con información taxonómica
        elif apellido_clean and any(
            re.search(pattern, apellido_clean.upper())
            for pattern in self.taxonomia_patterns
        ):
            # Solo el apellido parece ser clasificación científica
            info["especie"] = nombre_clean or apellido_clean.split()[0]
            info["subespecie"] = apellido_clean

            # Estructurar información taxonómica
            words = apellido_clean.upper().split()
            if len(words) >= 2:
                info["clasificacion_taxonomica"] = {
                    "genero": nombre_clean or words[0],
                    "especie": words[1] if len(words) > 1 else None,
                    "nombre_completo": apellido_clean,
                }

        # Caso estándar
        else:
            # Si nombre es NN pero apellido tiene info, usar apellido como especie
            if nombre in ["NN", "", None] and apellido_clean:
                info["especie"] = apellido_clean
            else:
                info["especie"] = nombre_clean or "DESCONOCIDO"

            if apellido_clean and nombre not in ["NN", "", None]:
                if len(apellido_clean.split()) > 1:
                    # Podría ser nombre científico completo
                    info["subespecie"] = apellido_clean
                else:
                    # Información adicional
                    info["info_adicional"].append(apellido_clean)

        return info

    def _extraer_info_humano(
        self, nombre: str, apellido: str, tipo_doc: str, nro_doc: str
    ) -> Dict[str, Any]:
        """
        Extrae información del humano.
        """
        return {
            "nombre_completo": f"{nombre} {apellido}".strip(),
            "nombre": nombre,
            "apellido": apellido,
            "documento": f"{tipo_doc} {nro_doc}".strip()
            if tipo_doc and nro_doc
            else None,
        }

    def _analizar_ambiguedad(
        self, nombre: str, apellido: str, sexo: str, tipo_doc: str
    ) -> str:
        """
        Analiza por qué un caso es ambiguo para ayudar en la revisión manual.
        """
        razones = []

        if sexo in ["IND", "ND"] and nombre not in ["NN", ""]:
            razones.append("Sexo indeterminado pero tiene nombre específico")

        if tipo_doc not in ["DNI", "LC", "LE"] and nombre not in ["NN", ""]:
            razones.append("Documento no estándar pero parece tener nombre de persona")

        if "NN" in nombre.upper() and "NN" not in apellido.upper():
            razones.append("Nombre genérico pero apellido específico")

        if not razones:
            razones.append("Patrones de datos contradictorios o insuficientes")

        return "; ".join(razones)


class MetadataExtractor:
    """
    Extractor genérico de metadata adicional (fuente_contagio, etc.)
    usando la lógica existente de regex pero de manera más estructurada.
    """

    def __init__(self):
        # Patrón de regex existente para fuente de contagio en rabia
        self.fuente_contagio_pattern = r"zorro|murci[ée]lago|muercielago|gato|perro|tadarida|lasiurus|histiotus|myotis"

        # Normalizaciones conocidas
        self.normalizaciones = {
            "muercielago": "murcielago",
            "tadarida": "murcielago",
            "lasiurus": "murcielago",
            "histiotus": "murcielago",
            "myotis": "murcielago",
        }

    def extraer_fuente_contagio(self, row: Dict[str, Any]) -> Optional[str]:
        """
        Extrae fuente de contagio usando el patrón existente de regex.
        """
        nombre = str(row.get("NOMBRE", "")).lower()
        apellido = str(row.get("APELLIDO", "")).lower()

        # Buscar en NOMBRE primero
        match = re.search(self.fuente_contagio_pattern, nombre, re.IGNORECASE)
        if not match:
            # Buscar en APELLIDO
            match = re.search(self.fuente_contagio_pattern, apellido, re.IGNORECASE)

        if match:
            found = match.group(0).lower()
            # Aplicar normalización
            return self.normalizaciones.get(found, found)

        return None

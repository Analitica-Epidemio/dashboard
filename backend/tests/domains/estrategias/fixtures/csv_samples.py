"""
Fixtures con casos reales extraídos de los CSVs de prueba y archivos legacy.
"""

from typing import Any, Dict, List

# Casos reales de Rabia Animal
RABIA_SAMPLES = [
    # Humano confirmado claro
    {
        "NOMBRE": "SANTINO GAEL",
        "APELLIDO": "MELLADO",
        "SEXO": "M",
        "TIPO_DOC": "DNI",
        "NRO_DOC": "45123456",
        "CLASIFICACION_MANUAL": "Caso confirmado",
        "EVENTO": "Rabia animal",
        "_expected_type": "humano",
        "_expected_classification": "confirmados",
    },
    # Animal confirmado - nomenclatura científica
    {
        "NOMBRE": "TADARIDA",
        "APELLIDO": "BRASILIENSIS",
        "SEXO": "IND",
        "TIPO_DOC": "",
        "NRO_DOC": "",
        "CLASIFICACION_MANUAL": "Caso confirmado",
        "EVENTO": "Rabia animal",
        "_expected_type": "animal",
        "_expected_classification": "confirmados",
    },
    # Animal con NN
    {
        "NOMBRE": "NN",
        "APELLIDO": "MURCIELAGO",
        "SEXO": "IND",
        "TIPO_DOC": "",
        "NRO_DOC": "",
        "CLASIFICACION_MANUAL": "Caso sospechoso",
        "EVENTO": "Rabia animal",
        "_expected_type": "animal",
        "_expected_classification": "sospechosos",
    },
    # Animal con ubicación
    {
        "NOMBRE": "ZORRO",
        "APELLIDO": "RUTA 25 KM 1234",
        "SEXO": "ND",
        "TIPO_DOC": "",
        "NRO_DOC": "",
        "CLASIFICACION_MANUAL": "Caso confirmado",
        "EVENTO": "Rabia animal",
        "_expected_type": "animal",
        "_expected_classification": "confirmados",
    },
    # Caso ambiguo - requiere revisión
    {
        "NOMBRE": "CARLOS",
        "APELLIDO": "RODRIGUEZ",
        "SEXO": "IND",  # Ambiguo: nombre humano pero sexo indeterminado
        "TIPO_DOC": "",
        "NRO_DOC": "",
        "CLASIFICACION_MANUAL": "Caso sospechoso",
        "EVENTO": "Rabia animal",
        "_expected_type": "indeterminado",
        "_expected_classification": "requiere_revision",
    },
]


# Casos reales de Dengue (del archivo legacy)
DENGUE_SAMPLES = [
    # Confirmado DEN-1
    {
        "NOMBRE": "MARIA",
        "APELLIDO": "GONZALEZ",
        "SEXO": "F",
        "TIPO_DOC": "DNI",
        "NRO_DOC": "33445566",
        "CLASIFICACION_MANUAL": "Caso confirmado DEN-1",
        "PROVINCIA_CARGA": "Chubut",
        "EVENTO": "Dengue",
        "_expected_classification": "confirmados",
    },
    # Confirmado DEN-2
    {
        "NOMBRE": "PEDRO",
        "APELLIDO": "MARTINEZ",
        "SEXO": "M",
        "TIPO_DOC": "DNI",
        "NRO_DOC": "22334455",
        "CLASIFICACION_MANUAL": "Caso confirmado DEN-2",
        "PROVINCIA_CARGA": "Chubut",
        "EVENTO": "Dengue",
        "_expected_classification": "confirmados",
    },
    # Confirmado sin serotipo
    {
        "NOMBRE": "ANA",
        "APELLIDO": "LOPEZ",
        "SEXO": "F",
        "TIPO_DOC": "DNI",
        "NRO_DOC": "11223344",
        "CLASIFICACION_MANUAL": "Caso confirmado sin serotipo",
        "PROVINCIA_CARGA": "Chubut",
        "EVENTO": "Dengue",
        "_expected_classification": "confirmados",
    },
    # Nexo epidemiológico autóctono
    {
        "NOMBRE": "LUIS",
        "APELLIDO": "FERNANDEZ",
        "SEXO": "M",
        "TIPO_DOC": "DNI",
        "NRO_DOC": "55667788",
        "CLASIFICACION_MANUAL": "Caso confirmado por nexo epidemiológico autóctono",
        "PROVINCIA_CARGA": "Chubut",
        "EVENTO": "Dengue",
        "_expected_classification": "confirmados",
    },
    # Sospechoso no conclusivo
    {
        "NOMBRE": "SOFIA",
        "APELLIDO": "TORRES",
        "SEXO": "F",
        "TIPO_DOC": "DNI",
        "NRO_DOC": "66778899",
        "CLASIFICACION_MANUAL": "Caso sospechoso no conclusivo",
        "PROVINCIA_CARGA": "Chubut",
        "EVENTO": "Dengue",
        "_expected_classification": "sospechosos",
    },
    # Caso probable
    {
        "NOMBRE": "DIEGO",
        "APELLIDO": "SILVA",
        "SEXO": "M",
        "TIPO_DOC": "DNI",
        "NRO_DOC": "77889900",
        "CLASIFICACION_MANUAL": "Caso probable",
        "PROVINCIA_CARGA": "Chubut",
        "EVENTO": "Dengue",
        "_expected_classification": "sospechosos",
    },
]


# Casos de Hepatitis B en gestantes
HEPATITIS_B_PER_GES_SAMPLES = [
    # Confirmado por resultado reactivo
    {
        "NOMBRE": "LAURA",
        "APELLIDO": "MARTINEZ",
        "SEXO": "F",
        "TIPO_DOC": "DNI",
        "NRO_DOC": "33456789",
        "RESULTADO": "Reactivo",
        "CLASIFICACION_MANUAL": "",  # Se confirma por resultado
        "EVENTO": "Hepatitis B en personas gestantes",
        "_expected_classification": "confirmados",
    },
    # Confirmado por clasificación manual
    {
        "NOMBRE": "ANDREA",
        "APELLIDO": "LOPEZ",
        "SEXO": "F",
        "TIPO_DOC": "DNI",
        "NRO_DOC": "44567890",
        "RESULTADO": "",
        "CLASIFICACION_MANUAL": "Caso CONFIRMADO de Infección Crónica por VHB",
        "EVENTO": "Hepatitis B en personas gestantes",
        "_expected_classification": "confirmados",
    },
    # Sospechoso en banco de sangre
    {
        "NOMBRE": "PATRICIA",
        "APELLIDO": "GONZALEZ",
        "SEXO": "F",
        "TIPO_DOC": "DNI",
        "NRO_DOC": "55678901",
        "RESULTADO": "",
        "CLASIFICACION_MANUAL": "Caso sospechoso en banco de sangre",
        "EVENTO": "Hepatitis B en personas gestantes",
        "_expected_classification": "sospechosos",
    },
]


# Casos reales de APR (del CSV subido)
APR_SAMPLES = [
    # Casos extraídos del CSV real
    {
        "NOMBRE": "ABDIEL UZIEL",
        "APELLIDO": "LLANCAPANI",
        "SEXO": "M",
        "TIPO_DOC": "DNI",
        "NRO_DOC": "12345678",
        "EVENTO": "Accidente potencialmente rábico (APR)",
        "_expected_type": "humano",
        "_expected_classification": "confirmados",  # APR todos son confirmados
    },
    {
        "NOMBRE": "AGUSTINA SOLANGE",
        "APELLIDO": "HARB",
        "SEXO": "F",
        "TIPO_DOC": "DNI",
        "NRO_DOC": "23456789",
        "EVENTO": "Accidente potencialmente rábico (APR)",
        "_expected_type": "humano",
        "_expected_classification": "confirmados",
    },
    {
        "NOMBRE": "AIMARA FRANCCESCA",
        "APELLIDO": "HUINCAHUEL",
        "SEXO": "F",
        "TIPO_DOC": "DNI",
        "NRO_DOC": "34567890",
        "EVENTO": "Accidente potencialmente rábico (APR)",
        "_expected_type": "humano",
        "_expected_classification": "confirmados",
    },
]


# Casos edge y problemáticos
EDGE_CASES = [
    # Valores nulos vs vacíos
    {
        "NOMBRE": None,
        "APELLIDO": "",
        "SEXO": "IND",
        "TIPO_DOC": None,
        "NRO_DOC": "",
        "CLASIFICACION_MANUAL": "Caso sospechoso",
        "_expected_type": "indeterminado",
    },
    # Espacios extras en clasificación
    {
        "NOMBRE": "JUAN",
        "APELLIDO": "PEREZ",
        "SEXO": "M",
        "TIPO_DOC": "DNI",
        "NRO_DOC": "12345678",
        "CLASIFICACION_MANUAL": " Caso confirmado ",  # Espacios extras
        "_expected_classification": "confirmados",
    },
    # Mayúsculas inconsistentes
    {
        "NOMBRE": "maria",  # lowercase
        "APELLIDO": "GONZALEZ",
        "SEXO": "f",  # lowercase
        "TIPO_DOC": "dni",  # lowercase
        "NRO_DOC": "87654321",
        "CLASIFICACION_MANUAL": "caso confirmado",  # lowercase
        "_expected_type": "humano",
    },
    # Número de documento muy largo (código interno)
    {
        "NOMBRE": "NN",
        "APELLIDO": "ANIMAL_SILVESTRE",
        "SEXO": "IND",
        "TIPO_DOC": "INTERNO",
        "NRO_DOC": "20230815001234567890",  # Muy largo
        "CLASIFICACION_MANUAL": "Caso confirmado",
        "_expected_type": "animal",
    },
]


def get_samples_by_event(event_name: str) -> List[Dict[str, Any]]:
    """Obtiene muestras por nombre de evento."""
    event_mapping = {
        "Rabia animal": RABIA_SAMPLES,
        "Dengue": DENGUE_SAMPLES,
        "Hepatitis B en personas gestantes": HEPATITIS_B_PER_GES_SAMPLES,
        "Accidente potencialmente rábico (APR)": APR_SAMPLES,
        "edge_cases": EDGE_CASES,
    }
    return event_mapping.get(event_name, [])


def get_all_samples() -> List[Dict[str, Any]]:
    """Obtiene todas las muestras disponibles."""
    all_samples = []
    all_samples.extend(RABIA_SAMPLES)
    all_samples.extend(DENGUE_SAMPLES)
    all_samples.extend(HEPATITIS_B_PER_GES_SAMPLES)
    all_samples.extend(APR_SAMPLES)
    all_samples.extend(EDGE_CASES)
    return all_samples

"""
Constantes geográficas para la provincia del Chubut
"""

# UGD (Unidades de Gestión Distrital - Ex Áreas Programáticas)
UGD_ZONA_NOROESTE = "Zona Noroeste"
UGD_ZONA_NORTE = "Zona Norte"
UGD_ZONA_SUR = "Zona Sur"
UGD_ZONA_NORESTE = "Zona Noreste"

LISTA_ZONAS_UGD = [
    UGD_ZONA_NOROESTE,
    UGD_ZONA_NORTE,
    UGD_ZONA_SUR,
    UGD_ZONA_NORESTE,
]

# Mapeo de códigos INDEC a nombres de departamentos
DEPARTAMENTOS_CHUBUT = {
    26007: "BIEDMA",
    26014: "CUSHAMEN",
    26021: "ESCALANTE",
    26028: "FLORENTINO AMEGHINO",
    26035: "FUTALEUFÚ",
    26042: "GAIMAN",
    26049: "GASTRE",
    26056: "LANGUIÑEO",
    26063: "MÁRTIRES",
    26070: "PASO DE INDIOS",
    26077: "RAWSON",
    26084: "RÍO SENGUER",
    26091: "SARMIENTO",
    26098: "TEHUELCHES",
    206105: "TELSEN",  # Nota: Este código parece incorrecto en el original
}

# Departamentos por zona UGD
UGD_DEPARTAMENTOS_POR_ZONA = {
    UGD_ZONA_NORESTE: [26077, 26042, 26028, 26063, 26070],  # RAWSON, GAIMAN, FLORENTINO AMEGHINO, MÁRTIRES, PASO DE INDIOS
    UGD_ZONA_NORTE: [26007, 206105, 26049],  # BIEDMA, TELSEN, GASTRE
    UGD_ZONA_SUR: [26021, 26091, 26084],  # ESCALANTE, SARMIENTO, RÍO SENGUER
    UGD_ZONA_NOROESTE: [26035, 26014, 26056, 26098],  # FUTALEUFÚ, CUSHAMEN, LANGUIÑEO, TEHUELCHES
}

# Población por departamento (Censo 2022)
POBLACION_DEPARTAMENTOS = {
    26007: 103173,   # BIEDMA
    26014: 28209,    # CUSHAMEN
    26021: 215453,   # ESCALANTE
    26028: 1786,     # FLORENTINO AMEGHINO
    26035: 50316,    # FUTALEUFÚ
    26042: 12639,    # GAIMAN
    26049: 1195,     # GASTRE
    26056: 2884,     # LANGUIÑEO
    26063: 754,      # MÁRTIRES
    26070: 1886,     # PASO DE INDIOS
    26077: 145763,   # RAWSON
    26084: 6366,     # RÍO SENGUER
    26091: 14596,    # SARMIENTO
    26098: 5978,     # TEHUELCHES
    206105: 1623,    # TELSEN
}

# Función helper para obtener la zona UGD de un departamento
def get_zona_ugd(id_departamento_indec: int) -> str:
    """Obtiene la zona UGD para un código de departamento INDEC"""
    for zona, departamentos in UGD_DEPARTAMENTOS_POR_ZONA.items():
        if id_departamento_indec in departamentos:
            return zona
    return "Sin zona asignada"

# Función helper para obtener el nombre del departamento
def get_nombre_departamento(id_departamento_indec: int) -> str:
    """Obtiene el nombre del departamento desde el código INDEC"""
    return DEPARTAMENTOS_CHUBUT.get(id_departamento_indec, f"Departamento INDEC {id_departamento_indec}")

# Función helper para obtener población
def get_poblacion_departamento(id_departamento_indec: int) -> int:
    """Obtiene la población del departamento"""
    return POBLACION_DEPARTAMENTOS.get(id_departamento_indec, 0)
"""
Parámetros epidemiológicos del sistema.

Factores de ajuste y grupos etarios estándar.
"""

# FACTORES DE AJUSTE EPIDEMIOLÓGICOS
AJUSTE_HAB = 100_000  # Factor por 100.000 habitantes
AJUSTE_100_HAB = 100  # Factor por 100 habitantes

# GRUPOS ETARIOS ESTÁNDAR
GRUPOS_ETARIOS = [
    "De 0 a 1 año",
    "De 1 a 2 años",
    "De 2 a 4 años",
    "De 5 a 9 años",
    "De 10 a 14 años",
    "De 15 a 19 años",
    "De 20 a 24 años",
    "De 25 a 34 años",
    "De 35 a 44 años",
    "De 45 a 65 años",
    "Mayores de 65 años",
]

# VALOR PARA DATOS FALTANTES
SIN_DATO = "*sin dato*"  # Los casos de la U6 aparecen como sin dato

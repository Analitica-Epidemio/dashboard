"""
👥🐕 SUJETOS EPIDEMIOLÓGICOS - SUPPORTING DOMAIN

Gestión de todos los sujetos (humanos y animales) involucrados
en eventos epidemiológicos y sus actividades relacionadas.

MÓDULOS:
├── ciudadanos_models.py  👤 Ciudadanos y demografía humana
├── animales_models.py    🐕 Animales en eventos epidemiológicos
└── viajes_models.py      ✈️ Viajes y desplazamientos (nexo epidemiológico)

AGGREGATE ROOTS:
- Ciudadano: Persona física involucrada en eventos
- Animal: Animal involucrado en eventos (zoonosis)
- Viaje: Desplazamiento con relevancia epidemiológica

BOUNDED CONTEXT:
Todos los sujetos vivos (humanos y animales) que pueden ser
afectados, portadores o vectores en eventos epidemiológicos,
incluyendo sus movimientos y datos demográficos.
"""

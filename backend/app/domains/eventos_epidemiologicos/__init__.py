"""
🦠 EVENTOS EPIDEMIOLÓGICOS - CORE DOMAIN

El dominio CENTRAL del sistema de vigilancia epidemiológica.

MÓDULOS:
├── eventos/            📋 Gestión de eventos epidemiológicos (ENO)
├── clasificacion/      🤖 Clasificación automática de eventos
└── ambitos_models.py   🏢 Ámbitos y lugares de concurrencia/exposición

AGGREGATE ROOTS:
- Evento: Entidad principal del sistema
- EventStrategy: Estrategias de clasificación
- AmbitosConcurrencia: Lugares de exposición/transmisión

BOUNDED CONTEXT:
Todo lo relacionado con eventos epidemiológicos, su clasificación
automática y los ámbitos donde ocurren o se propagan.
"""

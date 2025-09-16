"""
🦠 EPIDEMIOLOGÍA CHUBUT - Dominios de Negocio (FIXED)

Esta nueva estructura corrige los problemas conceptuales encontrados
en la arquitectura anterior, aplicando correctamente los principios DDD.

DOMINIOS POR BOUNDED CONTEXT:
├── autenticacion/              🔐 SUPPORTING - Usuarios y sesiones
├── sujetos_epidemiologicos/    👥🐕 SUPPORTING - Ciudadanos, animales y viajes
├── eventos_epidemiologicos/    🦠 CORE - Eventos, clasificación y ámbitos
├── atencion_medica/           ⚕️ SUPPORTING - Síntomas, diagnósticos, muestras
└── territorio/                🗺️ SUPPORTING - Geografía y establecimientos

PRINCIPIOS APLICADOS:
✅ Separación clara de responsabilidades
✅ Nombres que "gritan" el propósito del dominio
✅ Cohesión conceptual alta
✅ Acoplamiento bajo entre dominios
✅ Un archivo = Un concepto específico
✅ Imports corregidos y actualizados
"""
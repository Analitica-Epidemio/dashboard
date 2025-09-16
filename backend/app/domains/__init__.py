"""
🦠 DOMINIOS DE NEGOCIO - EPIDEMIOLOGÍA CHUBUT

Esta carpeta contiene SOLO dominios de negocio puros, sin dependencias técnicas.

DOMINIOS:
├── epidemiologia/     🔥 CORE DOMAIN - Corazón del sistema
├── personas/          👥 Supporting - Gestión de personas
├── territorio/        🗺️ Supporting - Contexto geográfico
├── clinica/          ⚕️ Supporting - Contexto médico
└── autenticacion/    🔐 Supporting - Gestión de usuarios

REGLAS:
- Cada dominio es INDEPENDIENTE
- NO pueden depender de features/
- Solo comunican via Domain Events
- Aggregate Roots bien definidos
"""
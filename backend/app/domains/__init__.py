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

# Import all models for Alembic auto-detection
# 🔐 AUTENTICACION DOMAIN
from app.domains.autenticacion.models import User, UserSession, UserLogin

# 👥 SUJETOS EPIDEMIOLOGICOS DOMAIN
from app.domains.sujetos_epidemiologicos.ciudadanos_models import (
    Ciudadano,
    CiudadanoDatos,
    CiudadanoDomicilio,
    CiudadanoComorbilidades,
)
from app.domains.sujetos_epidemiologicos.animales_models import Animal
from app.domains.sujetos_epidemiologicos.viajes_models import ViajesCiudadano

# 🦠 EVENTOS EPIDEMIOLOGICOS DOMAIN
from app.domains.eventos_epidemiologicos.eventos.models import (
    Evento,
    TipoEno,
    GrupoEno,
    DetalleEventoSintomas,
    AntecedenteEpidemiologico,
    AntecedentesEpidemiologicosEvento,
)
from app.domains.eventos_epidemiologicos.ambitos_models import (
    AmbitosConcurrenciaEvento,
)
from app.domains.eventos_epidemiologicos.clasificacion.models import (
    EventStrategy,
    FilterCondition,
    ClassificationRule,
    EventClassificationAudit,
    StrategyChangeLog,
    TipoClasificacion,
)

# ⚕️ ATENCION MEDICA DOMAIN
from app.domains.atencion_medica.salud_models import (
    Sintoma,
    Comorbilidad,
    Vacuna,
    VacunasCiudadano,
    Muestra,
    MuestraEvento,
    Tecnica,
    ResultadoTecnica,
    Determinacion,
)
from app.domains.atencion_medica.diagnosticos_models import (
    DiagnosticoEvento,
    EstudioEvento,
    InternacionEvento,
    TratamientoEvento,
)
from app.domains.atencion_medica.investigaciones_models import (
    InvestigacionEvento,
    ContactosNotificacion,
)

# 🗺️ TERRITORIO DOMAIN
from app.domains.territorio.geografia_models import (
    Provincia,
    Departamento,
    Localidad,
    Domicilio,
)
from app.domains.territorio.establecimientos_models import (
    Establecimiento,
)
from app.domains.territorio.capas_gis_models import (
    CapaHidrografia,
    CapaAreaUrbana,
)

# 📊 FEATURES MODELS (para detección de Alembic)
# Idealmente estos deberían estar en domains, pero por ahora están en features
from app.features.dashboard.models import (
    DashboardChart,
)
from app.features.procesamiento_archivos.models import (
    ProcessingJob,
)
from app.features.analitica.models import (
    DatamartEpidemiologia,
)

# Export all models for external access
__all__ = [
    # Autenticacion
    "User",
    "UserSession",
    "UserLogin",
    # Sujetos epidemiologicos
    "Ciudadano",
    "CiudadanoDatos",
    "CiudadanoDomicilio",
    "CiudadanoComorbilidades",
    "Animal",
    "ViajesCiudadano",
    # Eventos epidemiologicos
    "Evento",
    "TipoEno",
    "GrupoEno",
    "DetalleEventoSintomas",
    "AntecedenteEpidemiologico",
    "AntecedentesEpidemiologicosEvento",
    "AmbitosConcurrenciaEvento",
    "EventStrategy",
    "FilterCondition",
    "ClassificationRule",
    "EventClassificationAudit",
    "StrategyChangeLog",
    "TipoClasificacion",
    # Atencion medica
    "Sintoma",
    "Comorbilidad",
    "Vacuna",
    "VacunasCiudadano",
    "Muestra",
    "MuestraEvento",
    "Tecnica",
    "ResultadoTecnica",
    "Determinacion",
    "DiagnosticoEvento",
    "EstudioEvento",
    "InternacionEvento",
    "TratamientoEvento",
    "InvestigacionEvento",
    "ContactosNotificacion",
    # Territorio
    "Provincia",
    "Departamento",
    "Localidad",
    "Domicilio",
    "Establecimiento",
    "CapaHidrografia",
    "CapaAreaUrbana",
    # Features
    "DashboardChart",
    "ProcessingJob",
    "DatamartEpidemiologia",
]
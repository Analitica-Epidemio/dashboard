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
from app.domains.atencion_medica.diagnosticos_models import (
    DiagnosticoEvento,
    EstudioEvento,
    InternacionEvento,
    TratamientoEvento,
)
from app.domains.atencion_medica.investigaciones_models import (
    ContactosNotificacion,
    InvestigacionEvento,
)

# ⚕️ ATENCION MEDICA DOMAIN
from app.domains.atencion_medica.salud_models import (
    Comorbilidad,
    Determinacion,
    Muestra,
    MuestraEvento,
    ResultadoTecnica,
    Sintoma,
    Tecnica,
    Vacuna,
    VacunasCiudadano,
)
from app.domains.autenticacion.models import User, UserLogin, UserSession

# 📋 BOLETINES DOMAIN
from app.domains.boletines.models import (
    BoletinInstance,
    BoletinTemplate,
    QueryDefinition,
)
from app.domains.eventos_epidemiologicos.ambitos_models import (
    AmbitosConcurrenciaEvento,
)
from app.domains.eventos_epidemiologicos.clasificacion.models import (
    ClassificationRule,
    EventClassificationAudit,
    EventStrategy,
    FilterCondition,
    StrategyChangeLog,
    TipoClasificacion,
)

# 🦠 EVENTOS EPIDEMIOLOGICOS DOMAIN
from app.domains.eventos_epidemiologicos.eventos.models import (
    AntecedenteEpidemiologico,
    AntecedentesEpidemiologicosEvento,
    DetalleEventoSintomas,
    Evento,
    GrupoEno,
    TipoEno,
)
from app.domains.sujetos_epidemiologicos.animales_models import Animal

# 👥 SUJETOS EPIDEMIOLOGICOS DOMAIN
from app.domains.sujetos_epidemiologicos.ciudadanos_models import (
    Ciudadano,
    CiudadanoComorbilidades,
    CiudadanoDatos,
    CiudadanoDomicilio,
)
from app.domains.sujetos_epidemiologicos.viajes_models import ViajesCiudadano
from app.domains.territorio.capas_gis_models import (
    CapaAreaUrbana,
    CapaHidrografia,
)
from app.domains.territorio.establecimientos_models import (
    Establecimiento,
)

# 🗺️ TERRITORIO DOMAIN
from app.domains.territorio.geografia_models import (
    Departamento,
    Domicilio,
    Localidad,
    Provincia,
)
from app.features.analitica.models import (
    DatamartEpidemiologia,
)

# 📊 FEATURES MODELS (para detección de Alembic)
# Idealmente estos deberían estar en domains, pero por ahora están en features
from app.features.dashboard.models import (
    DashboardChart,
)
from app.features.procesamiento_archivos.models import (
    ProcessingJob,
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
    # Boletines
    "BoletinTemplate",
    "BoletinInstance",
    "QueryDefinition",
    # Features
    "DashboardChart",
    "ProcessingJob",
    "DatamartEpidemiologia",
]
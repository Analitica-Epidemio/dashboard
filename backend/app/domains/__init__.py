"""
EPIDEMIOLOGIA CHUBUT - Dominios de Negocio

DOMINIOS POR BOUNDED CONTEXT:
├── autenticacion/              Usuarios y sesiones
├── vigilancia_nominal/         Casos individuales (sujetos, atencion, clasificacion)
├── vigilancia_agregada/        Datos agregados (conteos semanales)
├── catalogos/                  Catálogos compartidos (agentes etiológicos)
├── territorio/                 Geografía y establecimientos
├── boletines/                  Generación de boletines
├── procesamiento/              Carga y procesamiento de archivos
├── dashboard/                  Configuración de dashboards
└── analitica/                  Servicios de métricas

PRINCIPIOS APLICADOS:
- Separación clara de responsabilidades
- Cohesión conceptual alta
- Acoplamiento bajo entre dominios
"""

# Import all models for Alembic auto-detection

# AUTENTICACION DOMAIN
from app.domains.autenticacion.models import User, UserLogin, UserSession

# CATALOGOS COMPARTIDOS
from app.domains.catalogos.agentes.models import (
    AgenteEtiologico,
    CategoriaAgente,
    GrupoAgente,
)

# VIGILANCIA NOMINAL DOMAIN (casos individuales)
# Incluye: sujetos, enfermedades, agentes, atención médica, clasificación
from app.domains.vigilancia_nominal.models import (
    # Caso (modelo central)
    AntecedenteEpidemiologico,
    AntecedentesCasoEpidemiologico,
    CasoEpidemiologico,
    CasoGrupoEnfermedad,
    DetalleCasoSintomas,
    # Enfermedades
    Enfermedad,
    EnfermedadGrupo,
    GrupoDeEnfermedades,
    # Sujetos
    Animal,
    Ciudadano,
    CiudadanoComorbilidades,
    CiudadanoDatos,
    CiudadanoDomicilio,
    PersonaDomicilio,
    ViajesCiudadano,
    # Agentes (detecciones)
    AgenteExtraccionConfig,
    CasoAgente,
    ResultadoDeteccion,
    # Atención médica
    ContactosNotificacion,
    DiagnosticoCasoEpidemiologico,
    InternacionCasoEpidemiologico,
    InvestigacionCasoEpidemiologico,
    TratamientoCasoEpidemiologico,
    # Salud (catálogos y registros)
    Comorbilidad,
    Determinacion,
    EstudioCasoEpidemiologico,
    Muestra,
    MuestraCasoEpidemiologico,
    ResultadoTecnica,
    Sintoma,
    Tecnica,
    Vacuna,
    VacunasCiudadano,
    # Ámbitos
    AmbitosConcurrenciaCaso,
)
from app.domains.vigilancia_nominal.clasificacion.models import (
    ClassificationRule,
    EstrategiaClasificacion,
    EventClassificationAudit,
    FilterCondition,
    StrategyChangeLog,
    TipoClasificacion,
)

# VIGILANCIA AGREGADA DOMAIN (datos agregados)
from app.domains.vigilancia_agregada.constants import (
    EstadoNotificacion,
    OrigenDatosPasivos,
    Sexo,
)
from app.domains.vigilancia_agregada.models.cargas import (
    NotificacionSemanal,
)
from app.domains.vigilancia_agregada.models.catalogos import (
    RangoEtario,
    TipoCasoEpidemiologicoPasivo,
)
from app.domains.vigilancia_agregada.models.conteos import (
    ConteoCamasIRA,
    ConteoCasosClinicos,
    ConteoEstudiosLab,
)

# TERRITORIO DOMAIN
from app.domains.territorio.capas_gis_models import (
    CapaAreaUrbana,
    CapaHidrografia,
)
from app.domains.territorio.establecimientos_models import (
    Establecimiento,
)
from app.domains.territorio.geografia_models import (
    Departamento,
    Domicilio,
    Localidad,
    Provincia,
)

# BOLETINES DOMAIN
from app.domains.boletines.models import (
    BoletinInstance,
    BoletinSnippet,
    BoletinTemplate,
    BoletinTemplateConfig,
    CapacidadHospitalaria,
    VirusRespiratorio,
)

# JOBS DOMAIN
from app.domains.jobs.models import Job

# DASHBOARD DOMAIN
from app.domains.dashboard.models import (
    DashboardChart,
)


# Export all models for external access
__all__ = [
    # Autenticacion
    "User",
    "UserSession",
    "UserLogin",
    # Catalogos compartidos
    "AgenteEtiologico",
    "CategoriaAgente",
    "GrupoAgente",
    # Vigilancia nominal - Caso
    "CasoEpidemiologico",
    "CasoGrupoEnfermedad",
    "DetalleCasoSintomas",
    "AntecedenteEpidemiologico",
    "AntecedentesCasoEpidemiologico",
    # Vigilancia nominal - Enfermedades
    "Enfermedad",
    "GrupoDeEnfermedades",
    "EnfermedadGrupo",
    # Vigilancia nominal - Sujetos
    "Ciudadano",
    "CiudadanoDatos",
    "CiudadanoDomicilio",
    "CiudadanoComorbilidades",
    "PersonaDomicilio",
    "Animal",
    "ViajesCiudadano",
    # Vigilancia nominal - Agentes
    "AgenteExtraccionConfig",
    "CasoAgente",
    "ResultadoDeteccion",
    # Vigilancia nominal - Clasificación
    "EstrategiaClasificacion",
    "FilterCondition",
    "ClassificationRule",
    "EventClassificationAudit",
    "StrategyChangeLog",
    "TipoClasificacion",
    # Vigilancia nominal - Atención médica
    "DiagnosticoCasoEpidemiologico",
    "InternacionCasoEpidemiologico",
    "TratamientoCasoEpidemiologico",
    "InvestigacionCasoEpidemiologico",
    "ContactosNotificacion",
    # Vigilancia nominal - Salud
    "Sintoma",
    "Comorbilidad",
    "Vacuna",
    "VacunasCiudadano",
    "Muestra",
    "MuestraCasoEpidemiologico",
    "EstudioCasoEpidemiologico",
    "Tecnica",
    "ResultadoTecnica",
    "Determinacion",
    # Vigilancia nominal - Ámbitos
    "AmbitosConcurrenciaCaso",
    # Vigilancia agregada
    "OrigenDatosPasivos",
    "RangoEtario",
    "TipoCasoEpidemiologicoPasivo",
    "EstadoNotificacion",
    "NotificacionSemanal",
    "ConteoCasosClinicos",
    "ConteoEstudiosLab",
    "ConteoCamasIRA",
    "Sexo",
    # Territorio
    "Provincia",
    "Departamento",
    "Localidad",
    "Domicilio",
    "Establecimiento",
    "CapaHidrografia",
    "CapaAreaUrbana",
    # Boletines
    "BoletinSnippet",
    "BoletinTemplate",
    "BoletinInstance",
    "BoletinTemplateConfig",
    "CapacidadHospitalaria",
    "VirusRespiratorio",
    # Features
    "DashboardChart",
    "Job",
]

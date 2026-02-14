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

# BOLETINES DOMAIN
from app.domains.boletines.models import (
    BoletinBloque,
    BoletinInstance,
    BoletinSeccion,
    BoletinSnippet,
    BoletinTemplate,
    BoletinTemplateConfig,
    CapacidadHospitalaria,
    VirusRespiratorio,
)

# CATALOGOS COMPARTIDOS
from app.domains.catalogos.agentes.models import (
    AgenteEtiologico,
    CategoriaAgente,
    GrupoAgente,
)

# DASHBOARD DOMAIN
from app.domains.dashboard.models import (
    DashboardChart,
)

# JOBS DOMAIN
from app.domains.jobs.models import Job

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
from app.domains.vigilancia_nominal.clasificacion.models import (
    ClassificationRule,
    EstrategiaClasificacion,
    EventClassificationAudit,
    FilterCondition,
    StrategyChangeLog,
    TipoClasificacion,
)

# VIGILANCIA NOMINAL DOMAIN (casos individuales)
# Incluye: sujetos, enfermedades, agentes, atención médica, clasificación
from app.domains.vigilancia_nominal.models import (
    # Agentes (detecciones)
    AgenteExtraccionConfig,
    # Ámbitos
    AmbitosConcurrenciaCaso,
    # Sujetos
    Animal,
    # Caso (modelo central)
    AntecedenteEpidemiologico,
    AntecedentesCasoEpidemiologico,
    CasoAgente,
    CasoEpidemiologico,
    CasoGrupoEnfermedad,
    Ciudadano,
    CiudadanoComorbilidades,
    CiudadanoDatos,
    CiudadanoDomicilio,
    # Salud (catálogos y registros)
    Comorbilidad,
    # Atención médica
    ContactosNotificacion,
    DetalleCasoSintomas,
    Determinacion,
    DiagnosticoCasoEpidemiologico,
    # Enfermedades
    Enfermedad,
    EnfermedadGrupo,
    EstudioCasoEpidemiologico,
    GrupoDeEnfermedades,
    InternacionCasoEpidemiologico,
    InvestigacionCasoEpidemiologico,
    Muestra,
    MuestraCasoEpidemiologico,
    PersonaDomicilio,
    ResultadoDeteccion,
    ResultadoTecnica,
    Sintoma,
    Tecnica,
    TratamientoCasoEpidemiologico,
    Vacuna,
    VacunasCiudadano,
    ViajesCiudadano,
)

# Export all models for external access
__all__ = [
    # Catalogos compartidos
    "AgenteEtiologico",
    # Vigilancia nominal - Agentes
    "AgenteExtraccionConfig",
    # Vigilancia nominal - Ámbitos
    "AmbitosConcurrenciaCaso",
    "Animal",
    "AntecedenteEpidemiologico",
    "AntecedentesCasoEpidemiologico",
    # Boletines
    "BoletinBloque",
    "BoletinInstance",
    "BoletinSeccion",
    "BoletinSnippet",
    "BoletinTemplate",
    "BoletinTemplateConfig",
    "CapaAreaUrbana",
    "CapaHidrografia",
    "CapacidadHospitalaria",
    "CasoAgente",
    # Vigilancia nominal - Caso
    "CasoEpidemiologico",
    "CasoGrupoEnfermedad",
    "CategoriaAgente",
    # Vigilancia nominal - Sujetos
    "Ciudadano",
    "CiudadanoComorbilidades",
    "CiudadanoDatos",
    "CiudadanoDomicilio",
    "ClassificationRule",
    "Comorbilidad",
    "ContactosNotificacion",
    "ConteoCamasIRA",
    "ConteoCasosClinicos",
    "ConteoEstudiosLab",
    # Features
    "DashboardChart",
    "Departamento",
    "DetalleCasoSintomas",
    "Determinacion",
    # Vigilancia nominal - Atención médica
    "DiagnosticoCasoEpidemiologico",
    "Domicilio",
    # Vigilancia nominal - Enfermedades
    "Enfermedad",
    "EnfermedadGrupo",
    "Establecimiento",
    "EstadoNotificacion",
    # Vigilancia nominal - Clasificación
    "EstrategiaClasificacion",
    "EstudioCasoEpidemiologico",
    "EventClassificationAudit",
    "FilterCondition",
    "GrupoAgente",
    "GrupoDeEnfermedades",
    "InternacionCasoEpidemiologico",
    "InvestigacionCasoEpidemiologico",
    "Job",
    "Localidad",
    "Muestra",
    "MuestraCasoEpidemiologico",
    "NotificacionSemanal",
    # Vigilancia agregada
    "OrigenDatosPasivos",
    "PersonaDomicilio",
    # Territorio
    "Provincia",
    "RangoEtario",
    "ResultadoDeteccion",
    "ResultadoTecnica",
    "Sexo",
    # Vigilancia nominal - Salud
    "Sintoma",
    "StrategyChangeLog",
    "Tecnica",
    "TipoCasoEpidemiologicoPasivo",
    "TipoClasificacion",
    "TratamientoCasoEpidemiologico",
    # Autenticacion
    "User",
    "UserLogin",
    "UserSession",
    "Vacuna",
    "VacunasCiudadano",
    "ViajesCiudadano",
    "VirusRespiratorio",
]

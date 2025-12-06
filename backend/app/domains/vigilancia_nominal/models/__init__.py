"""
Modelos de vigilancia nominal (casos individuales).

Estructura:
- caso.py: CasoEpidemiologico (modelo central) y relaciones directas
- enfermedad.py: Enfermedad, GrupoDeEnfermedades, EnfermedadGrupo
- sujetos.py: Ciudadano, Animal, ViajesCiudadano
- agentes.py: CasoAgente, AgenteExtraccionConfig (detecciones en casos)
- atencion.py: Diagnósticos, internaciones, tratamientos, investigaciones
- salud.py: Catálogos de salud (Sintoma, Vacuna, etc.) y muestras
- ambitos.py: AmbitosConcurrenciaCaso
"""

# Caso (modelo central)
# Agentes (detecciones)
from app.domains.vigilancia_nominal.models.agentes import (
    AgenteExtraccionConfig,
    CasoAgente,
    ResultadoDeteccion,
)

# Ámbitos
from app.domains.vigilancia_nominal.models.ambitos import (
    AmbitosConcurrenciaCaso,
)

# Atención médica
from app.domains.vigilancia_nominal.models.atencion import (
    ContactosNotificacion,
    DiagnosticoCasoEpidemiologico,
    InternacionCasoEpidemiologico,
    InvestigacionCasoEpidemiologico,
    TratamientoCasoEpidemiologico,
)
from app.domains.vigilancia_nominal.models.caso import (
    AntecedenteEpidemiologico,
    AntecedentesCasoEpidemiologico,
    CasoEpidemiologico,
    CasoGrupoEnfermedad,
    DetalleCasoSintomas,
)

# Enfermedades
from app.domains.vigilancia_nominal.models.enfermedad import (
    Enfermedad,
    EnfermedadGrupo,
    GrupoDeEnfermedades,
)

# Salud (catálogos y registros)
from app.domains.vigilancia_nominal.models.salud import (
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
)

# Sujetos
from app.domains.vigilancia_nominal.models.sujetos import (
    Animal,
    Ciudadano,
    CiudadanoComorbilidades,
    CiudadanoDatos,
    CiudadanoDomicilio,
    PersonaDomicilio,
    ViajesCiudadano,
)

__all__ = [
    # Caso
    "CasoEpidemiologico",
    "CasoGrupoEnfermedad",
    "DetalleCasoSintomas",
    "AntecedenteEpidemiologico",
    "AntecedentesCasoEpidemiologico",
    # Enfermedades
    "Enfermedad",
    "GrupoDeEnfermedades",
    "EnfermedadGrupo",
    # Sujetos
    "Ciudadano",
    "CiudadanoDatos",
    "CiudadanoDomicilio",
    "CiudadanoComorbilidades",
    "PersonaDomicilio",
    "Animal",
    "ViajesCiudadano",
    # Agentes
    "AgenteExtraccionConfig",
    "CasoAgente",
    "ResultadoDeteccion",
    # Atención
    "DiagnosticoCasoEpidemiologico",
    "InternacionCasoEpidemiologico",
    "TratamientoCasoEpidemiologico",
    "InvestigacionCasoEpidemiologico",
    "ContactosNotificacion",
    # Muestras y estudios
    "MuestraCasoEpidemiologico",
    "EstudioCasoEpidemiologico",
    # Catálogos de salud
    "Sintoma",
    "Comorbilidad",
    "Vacuna",
    "VacunasCiudadano",
    "Muestra",
    "Determinacion",
    "Tecnica",
    "ResultadoTecnica",
    # Ámbitos
    "AmbitosConcurrenciaCaso",
]

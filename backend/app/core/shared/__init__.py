"""Código compartido entre dominios."""

from .enums import (
    EstadoEventoEpidemiologico,
    EstadoInternacion,
    FrecuenciaOcurrencia,
    OrigenFinanciamiento,
    RespuestaSiNoIndeterminado,
    ResultadoTratamiento,
    SexoBiologico,
    TipoContactoEpidemiologico,
    TipoDocumento,
    TipoLugarOcurrencia,
)

__all__ = [
    "TipoDocumento",
    "SexoBiologico", 
    "RespuestaSiNoIndeterminado",
    "FrecuenciaOcurrencia",
    "OrigenFinanciamiento",
    "TipoLugarOcurrencia",
    "EstadoEventoEpidemiologico",
    "ResultadoTratamiento",
    "EstadoInternacion",
    "TipoContactoEpidemiologico"
]
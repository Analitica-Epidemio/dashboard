"""Enumeraciones para el sistema de epidemiología"""

from enum import Enum


class TipoDocumento(str, Enum):
    """Tipos de documento de identidad"""

    DNI = "DNI"
    LIBRETA_CIVICA = "LC"
    LIBRETA_ENROLAMIENTO = "LE"
    CEDULA_IDENTIDAD = "CI"
    PASAPORTE = "PAS"


class SexoBiologico(str, Enum):
    """Sexo biológico"""

    MASCULINO = "M"
    FEMENINO = "F"
    NO_ESPECIFICADO = "X"


class RespuestaSiNoIndeterminado(str, Enum):
    """Respuesta trinaria: Sí, No o Indeterminado"""

    SI = "SI"
    NO = "NO"
    NO_DETERMINADO = "ND"
    NO_SABE = "NS"

    def to_bool(self) -> bool | None:
        """Convierte a booleano (None si es indeterminado)"""
        if self == RespuestaSiNoIndeterminado.SI:
            return True
        elif self == RespuestaSiNoIndeterminado.NO:
            return False
        return None


class FrecuenciaOcurrencia(str, Enum):
    """Frecuencia con la que ocurre un evento"""

    UNICA_VEZ = "UNICA_VEZ"
    DIARIA = "DIARIA"
    SEMANAL = "SEMANAL"
    MENSUAL = "MENSUAL"
    ANUAL = "ANUAL"
    OCASIONAL = "OCASIONAL"


class OrigenFinanciamiento(str, Enum):
    """Origen del financiamiento de una investigación"""

    PUBLICO = "PUBLICO"
    PRIVADO = "PRIVADO"
    MIXTO = "MIXTO"


class TipoLugarOcurrencia(str, Enum):
    """Tipo de lugar donde ocurrió un evento epidemiológico"""

    DOMICILIO_PARTICULAR = "DOMICILIO"
    INSTITUCION_EDUCATIVA = "ESCUELA"
    LUGAR_TRABAJO = "TRABAJO"
    HOSPITAL = "HOSPITAL"
    CENTRO_SALUD = "CENTRO_SALUD"
    VIA_PUBLICA = "VIA_PUBLICA"
    TRANSPORTE_PUBLICO = "TRANSPORTE"
    OTRO = "OTRO"


class EstadoEventoEpidemiologico(str, Enum):
    """Estado de clasificación de un evento epidemiológico"""

    SOSPECHOSO = "SOSPECHOSO"
    CONFIRMADO = "CONFIRMADO"
    DESCARTADO = "DESCARTADO"
    EN_INVESTIGACION = "EN_INVESTIGACION"


class ResultadoTratamiento(str, Enum):
    """Resultado del tratamiento médico aplicado"""

    PACIENTE_CURADO = "CURADO"
    PACIENTE_MEJORADO = "MEJORADO"
    SIN_CAMBIOS = "SIN_CAMBIOS"
    PACIENTE_EMPEORADO = "EMPEORADO"
    PACIENTE_FALLECIDO = "FALLECIDO"
    ABANDONO_TRATAMIENTO = "ABANDONO"
    EN_TRATAMIENTO = "EN_TRATAMIENTO"


class EstadoInternacion(str, Enum):
    """Estado de internación del paciente"""

    INTERNADO = "INTERNADO"
    ALTA_MEDICA = "ALTA_MEDICA"
    FALLECIDO = "FALLECIDO"
    TRASLADADO = "TRASLADADO"
    FUGA = "FUGA"


class TipoContactoEpidemiologico(str, Enum):
    """Tipo de contacto epidemiológico"""

    CONTACTO_ESTRECHO = "CONTACTO_ESTRECHO"
    CONTACTO_CASUAL = "CONTACTO_CASUAL"
    SIN_CONTACTO = "SIN_CONTACTO"
    NO_DETERMINADO = "NO_DETERMINADO"

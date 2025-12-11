"""
Constantes y enumeraciones compartidas del sistema.

Este archivo contiene enums que son usados por múltiples dominios (3+).
Los enums específicos de un dominio deben estar en `domains/<nombre>/constants.py`.

Convención:
- Nombres de clase en PascalCase
- Valores de enum en UPPER_CASE
- Docstrings explicando el propósito
"""

from enum import Enum

# ═══════════════════════════════════════════════════════════════════════════════
# IDENTIFICACIÓN DE PERSONAS
# ═══════════════════════════════════════════════════════════════════════════════


class TipoDocumento(str, Enum):
    """Tipos de documento de identidad en Argentina."""

    DNI = "DNI"
    LIBRETA_CIVICA = "LC"
    LIBRETA_ENROLAMIENTO = "LE"
    CEDULA_IDENTIDAD = "CI"
    PASAPORTE = "PAS"


class SexoBiologico(str, Enum):
    """Sexo biológico registrado."""

    MASCULINO = "MASCULINO"
    FEMENINO = "FEMENINO"
    NO_ESPECIFICADO = "NO_ESPECIFICADO"


# ═══════════════════════════════════════════════════════════════════════════════
# RESPUESTAS GENÉRICAS
# ═══════════════════════════════════════════════════════════════════════════════


class RespuestaSiNoIndeterminado(str, Enum):
    """Respuesta trinaria: Sí, No o Indeterminado."""

    SI = "SI"
    NO = "NO"
    NO_DETERMINADO = "ND"
    NO_SABE = "NS"

    def to_bool(self) -> bool | None:
        """Convierte a booleano (None si es indeterminado)."""
        if self == RespuestaSiNoIndeterminado.SI:
            return True
        elif self == RespuestaSiNoIndeterminado.NO:
            return False
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# UBICACIÓN Y CONTEXTO
# ═══════════════════════════════════════════════════════════════════════════════


class FrecuenciaOcurrencia(str, Enum):
    """Frecuencia con la que ocurre un evento."""

    UNICA_VEZ = "UNICA_VEZ"
    DIARIA = "DIARIA"
    SEMANAL = "SEMANAL"
    MENSUAL = "MENSUAL"
    ANUAL = "ANUAL"
    OCASIONAL = "OCASIONAL"


class TipoLugarOcurrencia(str, Enum):
    """Tipo de lugar donde ocurrió un evento epidemiológico."""

    DOMICILIO_PARTICULAR = "DOMICILIO"
    INSTITUCION_EDUCATIVA = "ESCUELA"
    LUGAR_TRABAJO = "TRABAJO"
    HOSPITAL = "HOSPITAL"
    CENTRO_SALUD = "CENTRO_SALUD"
    VIA_PUBLICA = "VIA_PUBLICA"
    TRANSPORTE_PUBLICO = "TRANSPORTE"
    OTRO = "OTRO"


# ═══════════════════════════════════════════════════════════════════════════════
# ATENCIÓN MÉDICA
# ═══════════════════════════════════════════════════════════════════════════════


class OrigenFinanciamiento(str, Enum):
    """Origen del financiamiento de una investigación."""

    PUBLICO = "PUBLICO"
    PRIVADO = "PRIVADO"
    MIXTO = "MIXTO"


class EstadoInternacion(str, Enum):
    """Estado de internación del paciente."""

    INTERNADO = "INTERNADO"
    ALTA_MEDICA = "ALTA_MEDICA"
    FALLECIDO = "FALLECIDO"
    TRASLADADO = "TRASLADADO"
    FUGA = "FUGA"


class ResultadoTratamiento(str, Enum):
    """Resultado del tratamiento médico aplicado."""

    ADECUADO = "Adecuado (al menos 1 dosis al menos 30 días antes de FPP)"
    APLICADO = "Aplicado"
    CURADO = "Curado"
    DESCONOCIDO = "Desconocido"
    EN_TRATAMIENTO = "En tratamiento"
    EXITO_TRATAMIENTO = "Éxito del tratamiento"
    FALLECIDO = "Fallecido"
    FRACASO_TRATAMIENTO = "Fracaso del tratamiento"
    INADECUADO = "Inadecuado"
    NO_CORRESPONDE = "No corresponde"
    PENICILINA_BENZATINICA = "Penicilina Benzatínica única dosis"
    PERDIDA_SEGUIMIENTO = "Pérdida de seguimiento"
    SIN_TRATAMIENTO = "Sin tratamiento"
    TRASLADO = "Traslado"
    TRATAMIENTO_COMPLETO = "Tratamiento completo"
    TRATAMIENTO_EN_CURSO = "Tratamiento en curso"
    TRATAMIENTO_INCOMPLETO = "Tratamiento incompleto"
    TRATAMIENTO_INCOMPLETO_ABANDONO = "Tratamiento incompleto por abandono"


# ═══════════════════════════════════════════════════════════════════════════════
# EPIDEMIOLOGÍA
# ═══════════════════════════════════════════════════════════════════════════════


class EstadoCasoEpidemiologicoEpidemiologico(str, Enum):
    """Estado de clasificación de un evento epidemiológico."""

    SOSPECHOSO = "SOSPECHOSO"
    CONFIRMADO = "CONFIRMADO"
    DESCARTADO = "DESCARTADO"
    EN_INVESTIGACION = "EN_INVESTIGACION"


class TipoContactoEpidemiologico(str, Enum):
    """Tipo de contacto epidemiológico."""

    CONTACTO_ESTRECHO = "CONTACTO_ESTRECHO"
    CONTACTO_CASUAL = "CONTACTO_CASUAL"
    SIN_CONTACTO = "SIN_CONTACTO"
    NO_DETERMINADO = "NO_DETERMINADO"

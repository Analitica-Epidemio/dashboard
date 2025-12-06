"""
Constantes y enumeraciones del dominio de Vigilancia Agregada (Pasiva).

Vigilancia agregada maneja conteos semanales de establecimientos,
a diferencia de vigilancia nominal que maneja casos individuales.
"""

from enum import Enum


class EstadoNotificacion(str, Enum):
    """
    Estado de la notificación semanal según SNVS.

    - CARGADA_CON_CASOS: El establecimiento reportó casos > 0
    - CARGADA_SIN_CASOS: El establecimiento reportó explícitamente 0 casos
    - PENDIENTE: Aún no se procesó
    - ERROR: Error durante el procesamiento
    """

    CARGADA_CON_CASOS = "cargada_con_casos"
    CARGADA_SIN_CASOS = "cargada_sin_casos"
    PENDIENTE = "pendiente"
    ERROR = "error"


class OrigenDatosPasivos(str, Enum):
    """
    Origen de los datos de vigilancia pasiva.

    Cada origen corresponde a un archivo/reporte del SNVS.
    """

    CLINICO = "clinico"          # CLI_P26 - Casos clínicos
    LABORATORIO = "laboratorio"  # LAB_P26 - Estudios de laboratorio
    INTERNACION = "internacion"  # CLI_P26_INT - Internaciones IRA


class Sexo(str, Enum):
    """Sexo biológico en datos de vigilancia agregada."""

    MASCULINO = "M"
    FEMENINO = "F"
    SIN_ESPECIFICAR = "X"

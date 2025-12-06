"""
Enums específicos del dominio de Vigilancia Nominal.

Solo contiene enums que son específicos de este dominio y no existen en otro lugar.
Para enums compartidos, usar `app.core.shared.enums`.

Convención: Los enums de dominio se co-localizan aquí cuando son usados por
múltiples modelos dentro del dominio. Si un enum es usado solo por un modelo,
puede definirse junto al modelo.
"""

from enum import Enum


class ModalidadVigilancia(str, Enum):
    """
    Modalidad de vigilancia epidemiológica para una enfermedad.

    Define cómo se recolectan los datos de una enfermedad:
    - UNIVERSAL: Se notifican todos los casos (ej: Dengue, Rabia)
    - CENTINELA: Solo sitios centinela reportan (ej: Influenza)
    - LABORATORIAL: Requiere confirmación de laboratorio
    """

    UNIVERSAL = "universal"
    CENTINELA = "centinela"
    LABORATORIAL = "laboratorial"


class GravedadEnfermedad(str, Enum):
    """
    Clasificación de gravedad para priorización de respuesta.

    Define los tiempos de respuesta esperados:
    - CRITICA: Respuesta inmediata (<24h). Ej: Rabia, Cólera, Peste
    - ALTA: Respuesta rápida (<48h). Ej: Dengue grave, Meningitis
    - MEDIA: Seguimiento semanal. Ej: Dengue, Hepatitis
    - BAJA: Seguimiento mensual. Ej: Varicela, Parotiditis
    """

    CRITICA = "critica"
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"

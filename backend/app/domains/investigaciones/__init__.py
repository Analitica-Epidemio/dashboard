"""
Dominio de Investigaciones - Investigaciones epidemiológicas.

Contiene:
- Investigaciones epidemiológicas en terreno
- Eventos centinela y usuarios centinela
- Contactos y notificaciones
- Seguimiento de casos
"""

from .models import ContactosNotificacion, InvestigacionEvento

__all__ = ["InvestigacionEvento", "ContactosNotificacion"]

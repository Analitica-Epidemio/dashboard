"""
Resolucion de condiciones para mostrar charts segun codigos estables
"""

import logging
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.domains.dashboard.models import DashboardChart
from app.domains.vigilancia_nominal.models.enfermedad import (
    Enfermedad,
    GrupoDeEnfermedades,
)

logger = logging.getLogger(__name__)


class ChartConditionResolver:
    """
    Resuelve condiciones de visualización de charts usando códigos estables
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._grupo_cache = {}  # Cache para evitar múltiples queries
        self._tipo_cache = {}

    async def debe_mostrar_grafico(
        self, config_grafico: DashboardChart, filtros: Dict[str, Any]
    ) -> bool:
        """
        Determina si un chart debe mostrarse según las condiciones y filtros

        Args:
            config_grafico: Configuración del chart desde BD
            filtros: Filtros aplicados (grupo_id, evento_id, etc.)

        Returns:
            True si el chart debe mostrarse
        """
        if not config_grafico.condiciones_display:
            return True  # Sin condiciones = siempre mostrar

        condiciones = config_grafico.condiciones_display
        logger.debug(
            f"Evaluando condiciones para chart {config_grafico.codigo}: {condiciones}"
        )

        # Resolver condiciones por códigos de grupo
        if "grupo_codigos" in condiciones:
            codigos_permitidos = condiciones["grupo_codigos"]
            if not isinstance(codigos_permitidos, list):
                codigos_permitidos = [codigos_permitidos]

            if not await self._grupo_coincide_codigos(
                filtros.get("grupo_id"), codigos_permitidos
            ):
                logger.debug(
                    f"Chart {config_grafico.codigo} excluido por grupo_codigos"
                )
                return False

        # Resolver condiciones por códigos de tipo
        if "tipo_codigos" in condiciones:
            codigos_permitidos = condiciones["tipo_codigos"]
            if not isinstance(codigos_permitidos, list):
                codigos_permitidos = [codigos_permitidos]

            if not await self._tipo_coincide_codigos(
                filtros.get("evento_id"), codigos_permitidos
            ):
                logger.debug(f"Chart {config_grafico.codigo} excluido por tipo_codigos")
                return False

        # Otras condiciones futuras pueden agregarse aquí

        return True

    async def _grupo_coincide_codigos(
        self, grupo_id: Optional[int], codigos_permitidos: list
    ) -> bool:
        """
        Verifica si el grupo_id coincide con alguno de los códigos permitidos
        """
        if not grupo_id or not codigos_permitidos:
            return True

        # Usar cache si ya tenemos el grupo
        if grupo_id in self._grupo_cache:
            grupo_codigo = self._grupo_cache[grupo_id]
        else:
            # Consultar BD
            stmt = select(col(GrupoDeEnfermedades.slug)).where(
                col(GrupoDeEnfermedades.id) == grupo_id
            )
            result = await self.db.execute(stmt)
            grupo_codigo = result.scalar_one_or_none()

            if grupo_codigo:
                self._grupo_cache[grupo_id] = grupo_codigo
            else:
                logger.warning(f"Grupo con ID {grupo_id} no encontrado")
                return False

        return grupo_codigo in codigos_permitidos

    async def _tipo_coincide_codigos(
        self, tipo_id: Optional[int], codigos_permitidos: list
    ) -> bool:
        """
        Verifica si el tipo_id coincide con alguno de los códigos permitidos
        """
        if not tipo_id or not codigos_permitidos:
            return True

        # Usar cache si ya tenemos el tipo
        if tipo_id in self._tipo_cache:
            tipo_codigo = self._tipo_cache[tipo_id]
        else:
            # Consultar BD
            stmt = select(col(Enfermedad.slug)).where(col(Enfermedad.id) == tipo_id)
            result = await self.db.execute(stmt)
            tipo_codigo = result.scalar_one_or_none()

            if tipo_codigo:
                self._tipo_cache[tipo_id] = tipo_codigo
            else:
                logger.warning(f"Tipo con ID {tipo_id} no encontrado")
                return False

        return tipo_codigo in codigos_permitidos

    async def obtener_graficos_aplicables(
        self, filtros: Dict[str, Any], todos_los_graficos: list[DashboardChart]
    ) -> list[DashboardChart]:
        """
        Filtra una lista de charts según las condiciones y filtros

        Args:
            filtros: Filtros aplicados
            todos_los_graficos: Lista de DashboardChart

        Returns:
            Lista de charts que deben mostrarse
        """
        graficos_aplicables = []

        for grafico in todos_los_graficos:
            if not grafico.activo:
                continue

            if await self.debe_mostrar_grafico(grafico, filtros):
                graficos_aplicables.append(grafico)
            else:
                logger.debug(f"Chart {grafico.codigo} excluido por condiciones")

        return graficos_aplicables

    def limpiar_cache(self) -> None:
        """Limpia el cache interno"""
        self._grupo_cache.clear()
        self._tipo_cache.clear()

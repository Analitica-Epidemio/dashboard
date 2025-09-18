"""
Resolución de condiciones para mostrar charts según códigos estables
"""
import logging
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.dashboard.models import DashboardChart
from app.domains.eventos_epidemiologicos.eventos.models import GrupoEno, TipoEno

logger = logging.getLogger(__name__)


class ChartConditionResolver:
    """
    Resuelve condiciones de visualización de charts usando códigos estables
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._grupo_cache = {}  # Cache para evitar múltiples queries
        self._tipo_cache = {}
    
    async def chart_should_display(
        self, 
        chart_config: DashboardChart, 
        filtros: Dict[str, Any]
    ) -> bool:
        """
        Determina si un chart debe mostrarse según las condiciones y filtros
        
        Args:
            chart_config: Configuración del chart desde BD
            filtros: Filtros aplicados (grupo_id, evento_id, etc.)
            
        Returns:
            True si el chart debe mostrarse
        """
        if not chart_config.condiciones_display:
            return True  # Sin condiciones = siempre mostrar
        
        conditions = chart_config.condiciones_display
        logger.debug(f"Evaluando condiciones para chart {chart_config.codigo}: {conditions}")
        
        # Resolver condiciones por códigos de grupo
        if "grupo_codigos" in conditions:
            allowed_codes = conditions["grupo_codigos"]
            if not isinstance(allowed_codes, list):
                allowed_codes = [allowed_codes]
            
            if not await self._grupo_matches_codes(filtros.get("grupo_id"), allowed_codes):
                logger.debug(f"Chart {chart_config.codigo} excluido por grupo_codigos")
                return False
        
        # Resolver condiciones por códigos de tipo
        if "tipo_codigos" in conditions:
            allowed_codes = conditions["tipo_codigos"]
            if not isinstance(allowed_codes, list):
                allowed_codes = [allowed_codes]
            
            if not await self._tipo_matches_codes(filtros.get("evento_id"), allowed_codes):
                logger.debug(f"Chart {chart_config.codigo} excluido por tipo_codigos")
                return False
        
        # Otras condiciones futuras pueden agregarse aquí
        
        return True
    
    async def _grupo_matches_codes(self, grupo_id: Optional[int], allowed_codes: list) -> bool:
        """
        Verifica si el grupo_id coincide con alguno de los códigos permitidos
        """
        if not grupo_id or not allowed_codes:
            return True
        
        # Usar cache si ya tenemos el grupo
        if grupo_id in self._grupo_cache:
            grupo_codigo = self._grupo_cache[grupo_id]
        else:
            # Consultar BD
            stmt = select(GrupoEno.codigo).where(GrupoEno.id == grupo_id)
            result = await self.db.execute(stmt)
            grupo_codigo = result.scalar_one_or_none()
            
            if grupo_codigo:
                self._grupo_cache[grupo_id] = grupo_codigo
            else:
                logger.warning(f"Grupo con ID {grupo_id} no encontrado")
                return False
        
        return grupo_codigo in allowed_codes
    
    async def _tipo_matches_codes(self, tipo_id: Optional[int], allowed_codes: list) -> bool:
        """
        Verifica si el tipo_id coincide con alguno de los códigos permitidos
        """
        if not tipo_id or not allowed_codes:
            return True
        
        # Usar cache si ya tenemos el tipo
        if tipo_id in self._tipo_cache:
            tipo_codigo = self._tipo_cache[tipo_id]
        else:
            # Consultar BD
            stmt = select(TipoEno.codigo).where(TipoEno.id == tipo_id)
            result = await self.db.execute(stmt)
            tipo_codigo = result.scalar_one_or_none()
            
            if tipo_codigo:
                self._tipo_cache[tipo_id] = tipo_codigo
            else:
                logger.warning(f"Tipo con ID {tipo_id} no encontrado")
                return False
        
        return tipo_codigo in allowed_codes
    
    async def get_applicable_charts(
        self, 
        filtros: Dict[str, Any], 
        all_charts: list
    ) -> list:
        """
        Filtra una lista de charts según las condiciones y filtros
        
        Args:
            filtros: Filtros aplicados
            all_charts: Lista de DashboardChart
            
        Returns:
            Lista de charts que deben mostrarse
        """
        applicable_charts = []
        
        for chart in all_charts:
            if not chart.activo:
                continue
                
            if await self.chart_should_display(chart, filtros):
                applicable_charts.append(chart)
            else:
                logger.debug(f"Chart {chart.codigo} excluido por condiciones")
        
        return applicable_charts
    
    def clear_cache(self):
        """Limpia el cache interno"""
        self._grupo_cache.clear()
        self._tipo_cache.clear()
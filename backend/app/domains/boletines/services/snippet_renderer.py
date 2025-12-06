"""
Snippet Renderer Service
Renderiza snippets de boletines con placeholders usando Jinja2
"""

import logging
from typing import Any, Dict, List, Optional

from jinja2 import Environment, TemplateSyntaxError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.domains.boletines.models import BoletinSnippet

logger = logging.getLogger(__name__)


class SnippetRenderer:
    """
    Servicio para renderizar snippets de boletines con Jinja2.

    Los snippets son templates HTML con placeholders que se reemplazan
    con valores dinámicos basados en datos epidemiológicos.
    """

    def __init__(self) -> None:
        # Configurar entorno de Jinja2
        self.jinja_env = Environment(
            autoescape=True,  # Escapar HTML automáticamente para seguridad
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, snippet: BoletinSnippet, variables: Dict[str, Any]) -> str:
        """
        Renderiza un snippet con las variables proporcionadas.

        Args:
            snippet: El snippet a renderizar
            variables: Diccionario con valores para los placeholders

        Returns:
            HTML renderizado

        Raises:
            TemplateSyntaxError: Si el template tiene errores de sintaxis
            KeyError: Si falta una variable requerida
        """
        try:
            template = self.jinja_env.from_string(snippet.template)
            rendered = template.render(**variables)
            logger.debug(f"Snippet '{snippet.codigo}' renderizado exitosamente")
            return rendered

        except TemplateSyntaxError as e:
            logger.error(f"Error de sintaxis en snippet '{snippet.codigo}': {e}")
            raise

        except KeyError as e:
            logger.error(f"Variable faltante en snippet '{snippet.codigo}': {e}")
            raise

    async def get_snippet_by_codigo(
        self, db: AsyncSession, codigo: str
    ) -> Optional[BoletinSnippet]:
        """
        Obtiene un snippet por su código.

        Args:
            db: Sesión de base de datos
            codigo: Código único del snippet

        Returns:
            El snippet encontrado o None
        """
        query = select(BoletinSnippet).where(
            col(BoletinSnippet.codigo) == codigo,
            col(BoletinSnippet.is_active).is_(True),
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_snippets_by_categoria(
        self, db: AsyncSession, categoria: str
    ) -> List[BoletinSnippet]:
        """
        Obtiene todos los snippets de una categoría.

        Args:
            db: Sesión de base de datos
            categoria: Categoría de snippets

        Returns:
            Lista de snippets ordenados por 'orden'
        """
        query = (
            select(BoletinSnippet)
            .where(
                col(BoletinSnippet.categoria) == categoria,
                col(BoletinSnippet.is_active).is_(True),
            )
            .order_by(col(BoletinSnippet.orden))
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    def get_applicable_snippets(
        self, snippets: List[BoletinSnippet], context: Dict[str, Any]
    ) -> List[BoletinSnippet]:
        """
        Filtra snippets basándose en sus condiciones.

        Args:
            snippets: Lista de snippets a filtrar
            context: Contexto con datos para evaluar condiciones

        Returns:
            Lista de snippets que cumplen sus condiciones

        Ejemplo de condiciones en snippet:
        {
            "tipo_cambio": "crecimiento",
            "porcentaje_min": 50
        }

        Context debe incluir los valores necesarios:
        {
            "tipo_cambio": "crecimiento",
            "diferencia_porcentual": 87.5
        }
        """
        applicable = []

        for snippet in snippets:
            if snippet.condiciones is None or not snippet.condiciones:
                # Sin condiciones = siempre aplicable
                applicable.append(snippet)
                continue

            # Evaluar todas las condiciones
            matches = True
            for key, expected_value in snippet.condiciones.items():
                context_value = context.get(key)

                if context_value is None:
                    matches = False
                    break

                # Manejar diferentes tipos de condiciones
                if isinstance(expected_value, dict):
                    # Condiciones con operadores (ej: {"min": 50, "max": 100})
                    if (
                        "min" in expected_value
                        and context_value < expected_value["min"]
                    ):
                        matches = False
                        break
                    if (
                        "max" in expected_value
                        and context_value > expected_value["max"]
                    ):
                        matches = False
                        break
                else:
                    # Condición de igualdad simple
                    if context_value != expected_value:
                        matches = False
                        break

            if matches:
                applicable.append(snippet)

        logger.debug(
            f"Filtrados {len(applicable)}/{len(snippets)} snippets "
            f"aplicables para contexto"
        )

        return applicable

    async def render_snippet_by_codigo(
        self, db: AsyncSession, codigo: str, variables: Dict[str, Any]
    ) -> Optional[str]:
        """
        Renderiza un snippet buscándolo por código.

        Args:
            db: Sesión de base de datos
            codigo: Código del snippet
            variables: Variables para renderizar

        Returns:
            HTML renderizado o None si no se encuentra el snippet
        """
        snippet = await self.get_snippet_by_codigo(db, codigo)
        if not snippet:
            logger.warning(f"Snippet con código '{codigo}' no encontrado")
            return None

        return self.render(snippet, variables)

    def validate_variables(
        self, snippet: BoletinSnippet, variables: Dict[str, Any]
    ) -> List[str]:
        """
        Valida que todas las variables requeridas estén presentes.

        Args:
            snippet: Snippet a validar
            variables: Variables proporcionadas

        Returns:
            Lista de variables faltantes (vacía si todas están presentes)
        """
        required_vars = set(snippet.variables_schema.keys())
        provided_vars = set(variables.keys())
        missing = required_vars - provided_vars

        if missing:
            logger.warning(
                f"Variables faltantes en snippet '{snippet.codigo}': {missing}"
            )

        return list(missing)


# Singleton instance
snippet_renderer = SnippetRenderer()

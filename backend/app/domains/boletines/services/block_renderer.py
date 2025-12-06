"""
Servicio de renderizado de bloques para boletines.
Convierte datos de queries en TipTap JSON nativo (100% editable).
"""

import logging
from typing import Any

from jinja2 import BaseLoader, Environment, Undefined

logger = logging.getLogger(__name__)


class SilentUndefined(Undefined):
    """Custom Undefined que retorna string vacío en lugar de error."""

    def _fail_with_undefined_error(self, *args, **kwargs):
        return ""

    def __str__(self):
        return ""

    def __iter__(self):
        return iter([])

    def __bool__(self):
        return False


# Jinja2 environment para renderizar templates
_jinja_env = Environment(
    loader=BaseLoader(),
    autoescape=False,  # No escapamos HTML porque generamos JSON
    undefined=SilentUndefined,  # Variables no definidas = string vacío
)


def render_template(template_str: str, context: dict[str, Any]) -> str:
    """
    Renderiza un template string con Jinja2.

    Args:
        template_str: String con placeholders {{ variable }}
        context: Dict con valores de variables

    Returns:
        String con variables reemplazadas

    Variables disponibles:
        - semana: Semana epidemiológica actual
        - anio: Año
        - num_semanas: Cantidad de semanas analizadas
        - semana_inicio: Primera semana del período
        - fecha_inicio: Fecha de inicio (ISO format)
        - fecha_fin: Fecha de fin (ISO format)
        - tipo_evento: Nombre del tipo de evento (si aplica)
    """
    if not template_str:
        return template_str

    try:
        template = _jinja_env.from_string(template_str)
        return template.render(**context)
    except Exception as e:
        logger.warning(f"Error renderizando template: {e}")
        return template_str


class BoletinBlockRenderer:
    """
    Convierte datos de queries en TipTap JSON nativo.
    Todo el contenido generado es 100% editable en TipTap.
    """

    @staticmethod
    def render_top_enos_table(
        data: list[dict[str, Any]],
        config: dict[str, Any],
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Genera tabla TipTap nativa con top ENOs.

        Args:
            data: Lista de ENOs con casos y comparaciones
            config: {
                "titulo": "Top {{ limit }} ENOs en las últimas {{ num_semanas }} semanas",
                "include_comparison": true
            }
            context: Variables para renderizar templates (semana, anio, num_semanas, etc.)

        Returns:
            TipTap JSON con heading + table nativa
        """
        logger.info(f"Renderizando tabla top ENOs: {len(data)} eventos")
        ctx = context or {}

        # Renderizar título con variables
        titulo_template = config.get("titulo", "Top ENOs")
        titulo = render_template(titulo_template, ctx)

        if not data:
            return {
                "type": "paragraph",
                "content": [{
                    "type": "text",
                    "text": f"⚠️ {titulo}: No hay datos disponibles para el período seleccionado."
                }]
            }

        # Título
        content_nodes = [
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{
                    "type": "text",
                    "text": titulo
                }]
            }
        ]

        # Definir columnas según configuración
        include_comparison = config.get("include_comparison", True)

        # Headers de la tabla
        table_headers = [
            {"type": "text", "text": "ENO"},
            {"type": "text", "text": "Grupo"},
            {"type": "text", "text": "Casos"}
        ]

        if include_comparison:
            table_headers.extend([
                {"type": "text", "text": "Anterior"},
                {"type": "text", "text": "Cambio"},
                {"type": "text", "text": "Tendencia"}
            ])

        # Construir tabla TipTap nativa
        table_rows = [
            # Header row
            {
                "type": "tableRow",
                "content": [
                    {
                        "type": "tableHeader",
                        "content": [{"type": "paragraph", "content": [header]}]
                    }
                    for header in table_headers
                ]
            }
        ]

        # Data rows
        for row in data:
            cells = [
                {
                    "type": "tableCell",
                    "content": [{
                        "type": "paragraph",
                        "content": [{"type": "text", "text": row["tipo_eno_nombre"]}]
                    }]
                },
                {
                    "type": "tableCell",
                    "content": [{
                        "type": "paragraph",
                        "content": [{"type": "text", "text": row["grupo_eno_nombre"]}]
                    }]
                },
                {
                    "type": "tableCell",
                    "content": [{
                        "type": "paragraph",
                        "content": [{"type": "text", "text": str(row["casos_actuales"])}]
                    }]
                }
            ]

            if include_comparison:
                # Celda casos anteriores
                cells.append({
                    "type": "tableCell",
                    "content": [{
                        "type": "paragraph",
                        "content": [{"type": "text", "text": str(row["casos_previos"])}]
                    }]
                })

                # Celda cambio porcentual
                cambio_text = f"{row['cambio_porcentual']:+.1f}%"
                cells.append({
                    "type": "tableCell",
                    "content": [{
                        "type": "paragraph",
                        "content": [{"type": "text", "text": cambio_text}]
                    }]
                })

                # Celda tendencia
                tendencia_emoji = {
                    "crecimiento": "↑",
                    "descenso": "↓",
                    "estable": "→"
                }.get(row["tendencia"], "→")

                cells.append({
                    "type": "tableCell",
                    "content": [{
                        "type": "paragraph",
                        "content": [{"type": "text", "text": f"{tendencia_emoji} {row['tendencia'].title()}"}]
                    }]
                })

            table_rows.append({
                "type": "tableRow",
                "content": cells
            })

        # Agregar tabla completa
        content_nodes.append({
            "type": "table",
            "content": table_rows
        })

        # Agregar espacio después
        content_nodes.append({
            "type": "paragraph",
            "content": []
        })

        logger.info(f"✓ Tabla top ENOs renderizada: {len(data)} filas")

        return {
            "type": "doc",
            "content": content_nodes
        }

    @staticmethod
    def render_evento_section(
        data: dict[str, Any],
        config: dict[str, Any],
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Genera sección completa de evento con stats y charts.

        Args:
            data: Datos del evento (casos, distribuciones, etc.)
            config: {
                "titulo_template": "{{evento_nombre}}: Análisis SE {{semana}}",
                "charts": [...]
            }
            context: {semana, anio, evento_nombre, etc.}

        Returns:
            TipTap JSON con sección completa
        """
        logger.info(f"Renderizando sección evento: {data.get('tipo_eno_nombre')}")

        # Reemplazar variables en título
        titulo = config.get("titulo_template", "Análisis de CasoEpidemiologico")
        titulo = titulo.replace("{{evento_nombre}}", data.get("tipo_eno_nombre", "CasoEpidemiologico"))
        titulo = titulo.replace("{{semana}}", str(context.get("semana", "")))
        titulo = titulo.replace("{{anio}}", str(context.get("anio", "")))

        content_nodes = [
            # Título de sección
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{"type": "text", "text": titulo}]
            },
            # Párrafo introductorio
            {
                "type": "paragraph",
                "content": [{
                    "type": "text",
                    "text": f"Durante el período analizado se registraron {data.get('casos_totales', 0)} casos de {data.get('tipo_eno_nombre', 'este evento')}."
                }]
            }
        ]

        # Agregar charts dinámicos si están configurados
        charts_config = config.get("charts", [])
        for chart in charts_config:
            content_nodes.append({
                "type": "paragraph",
                "content": [{
                    "type": "dynamicChart",
                    "attrs": {
                        "chartCode": chart["code"],
                        "title": f"{data.get('tipo_eno_nombre')} - {chart['code']}",
                        "eventoIds": str(data.get("tipo_eno_id", "")),
                        "fechaDesde": context.get("fecha_inicio", ""),
                        "fechaHasta": context.get("fecha_fin", ""),
                        "height": chart.get("height", 400)
                    }
                }]
            })

        # Espacio al final
        content_nodes.append({
            "type": "paragraph",
            "content": []
        })

        logger.info(f"✓ Sección evento renderizada: {len(charts_config)} charts")

        return {
            "type": "doc",
            "content": content_nodes
        }

    @staticmethod
    def render_capacidad_table(
        data: list[dict[str, Any]],
        config: dict[str, Any],
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Genera tabla TipTap nativa con capacidad hospitalaria por UGD.

        Args:
            data: Lista de capacidad por UGD
            config: {"titulo": "Capacidad Hospitalaria SE {{ semana }}"}
            context: Variables para renderizar templates

        Returns:
            TipTap JSON con heading + table
        """
        logger.info(f"Renderizando tabla capacidad: {len(data)} UGDs")
        ctx = context or {}

        titulo_template = config.get("titulo", "Capacidad Hospitalaria")
        titulo = render_template(titulo_template, ctx)

        if not data:
            return {
                "type": "paragraph",
                "content": [{
                    "type": "text",
                    "text": f"⚠️ {titulo}: No hay datos disponibles."
                }]
            }

        content_nodes = [
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{
                    "type": "text",
                    "text": titulo
                }]
            }
        ]

        # Construir tabla
        table_rows = [
            # Header
            {
                "type": "tableRow",
                "content": [
                    {
                        "type": "tableHeader",
                        "content": [{
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "UGD"}]
                        }]
                    },
                    {
                        "type": "tableHeader",
                        "content": [{
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Camas Totales"}]
                        }]
                    },
                    {
                        "type": "tableHeader",
                        "content": [{
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Camas Ocupadas"}]
                        }]
                    },
                    {
                        "type": "tableHeader",
                        "content": [{
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "% Ocupación"}]
                        }]
                    }
                ]
            }
        ]

        # Data rows
        for row in data:
            table_rows.append({
                "type": "tableRow",
                "content": [
                    {
                        "type": "tableCell",
                        "content": [{
                            "type": "paragraph",
                            "content": [{"type": "text", "text": row["ugd"]}]
                        }]
                    },
                    {
                        "type": "tableCell",
                        "content": [{
                            "type": "paragraph",
                            "content": [{"type": "text", "text": str(row["camas_totales"])}]
                        }]
                    },
                    {
                        "type": "tableCell",
                        "content": [{
                            "type": "paragraph",
                            "content": [{"type": "text", "text": str(row["camas_ocupadas"])}]
                        }]
                    },
                    {
                        "type": "tableCell",
                        "content": [{
                            "type": "paragraph",
                            "content": [{"type": "text", "text": f"{row['porcentaje_ocupacion']:.1f}%"}]
                        }]
                    }
                ]
            })

        content_nodes.append({
            "type": "table",
            "content": table_rows
        })

        content_nodes.append({
            "type": "paragraph",
            "content": []
        })

        logger.info(f"✓ Tabla capacidad renderizada: {len(data)} filas")

        return {
            "type": "doc",
            "content": content_nodes
        }

    @staticmethod
    def render_virus_table(
        data: list[dict[str, Any]],
        config: dict[str, Any],
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Genera tabla TipTap nativa con detección de virus respiratorios.

        Args:
            data: Lista de virus con positividad
            config: {"titulo": "Detección de Virus SE {{ semana }}"}
            context: Variables para renderizar templates

        Returns:
            TipTap JSON con heading + table
        """
        logger.info(f"Renderizando tabla virus: {len(data)} tipos")
        ctx = context or {}

        titulo_template = config.get("titulo", "Virus Respiratorios")
        titulo = render_template(titulo_template, ctx)

        if not data:
            return {
                "type": "paragraph",
                "content": [{
                    "type": "text",
                    "text": f"⚠️ {titulo}: No hay datos disponibles."
                }]
            }

        content_nodes = [
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{
                    "type": "text",
                    "text": titulo
                }]
            }
        ]

        # Construir tabla
        table_rows = [
            # Header
            {
                "type": "tableRow",
                "content": [
                    {
                        "type": "tableHeader",
                        "content": [{
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Virus"}]
                        }]
                    },
                    {
                        "type": "tableHeader",
                        "content": [{
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Positivos"}]
                        }]
                    },
                    {
                        "type": "tableHeader",
                        "content": [{
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Testeados"}]
                        }]
                    },
                    {
                        "type": "tableHeader",
                        "content": [{
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "% Positividad"}]
                        }]
                    }
                ]
            }
        ]

        # Data rows
        for row in data:
            table_rows.append({
                "type": "tableRow",
                "content": [
                    {
                        "type": "tableCell",
                        "content": [{
                            "type": "paragraph",
                            "content": [{"type": "text", "text": row["virus_tipo"]}]
                        }]
                    },
                    {
                        "type": "tableCell",
                        "content": [{
                            "type": "paragraph",
                            "content": [{"type": "text", "text": str(row["casos_positivos"])}]
                        }]
                    },
                    {
                        "type": "tableCell",
                        "content": [{
                            "type": "paragraph",
                            "content": [{"type": "text", "text": str(row["casos_testeados"])}]
                        }]
                    },
                    {
                        "type": "tableCell",
                        "content": [{
                            "type": "paragraph",
                            "content": [{"type": "text", "text": f"{row['porcentaje_positividad']:.1f}%"}]
                        }]
                    }
                ]
            })

        content_nodes.append({
            "type": "table",
            "content": table_rows
        })

        content_nodes.append({
            "type": "paragraph",
            "content": []
        })

        logger.info(f"✓ Tabla virus renderizada: {len(data)} filas")

        return {
            "type": "doc",
            "content": content_nodes
        }

    @staticmethod
    def render_eventos_agrupados_table(
        data: dict[str, Any],
        config: dict[str, Any],
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Genera tabla TipTap nativa con eventos agrupados (ETI, Neumonía, etc).

        Args:
            data: Datos de eventos agrupados con corredor
            config: {"titulo": "Corredor endémico de {{ tipo_evento }} - SE {{ semana }}"}
            context: Variables para renderizar templates

        Returns:
            TipTap JSON con heading + descripción + table
        """
        logger.info(f"Renderizando tabla eventos agrupados: {data.get('evento')}")
        ctx = context or {}

        # Agregar tipo_evento al contexto si está en data
        if data.get("evento"):
            ctx = {**ctx, "tipo_evento": data.get("evento")}

        titulo_template = config.get("titulo", "CasoEpidemiologicos Agrupados")
        titulo = render_template(titulo_template, ctx)

        content_nodes = [
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{
                    "type": "text",
                    "text": titulo
                }]
            },
            {
                "type": "paragraph",
                "content": [{
                    "type": "text",
                    "text": f"Se registraron {data.get('casos_semana_actual', 0)} casos en la semana {data.get('semana_actual', '')}."
                }]
            }
        ]

        # Nota sobre corredor endémico
        if data.get("corredor"):
            content_nodes.append({
                "type": "paragraph",
                "content": [{
                    "type": "text",
                    "text": "Los datos se encuentran dentro del corredor endémico esperado para esta época del año."
                }]
            })

        content_nodes.append({
            "type": "paragraph",
            "content": []
        })

        logger.info("✓ Tabla eventos agrupados renderizada")

        return {
            "type": "doc",
            "content": content_nodes
        }

    @staticmethod
    def render_tabla_contenidos(
        secciones: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Genera índice de contenidos automático.

        Args:
            secciones: [
                {"titulo": "Resumen Ejecutivo", "nivel": 1},
                {"titulo": "Dengue", "nivel": 2},
                ...
            ]

        Returns:
            TipTap JSON con lista numerada
        """
        logger.info(f"Renderizando tabla de contenidos: {len(secciones)} secciones")

        content_nodes = [
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{
                    "type": "text",
                    "text": "Índice de Contenidos"
                }]
            }
        ]

        # Lista ordenada
        list_items = []
        for seccion in secciones:
            indent = "  " * (seccion.get("nivel", 1) - 1)
            list_items.append({
                "type": "listItem",
                "content": [{
                    "type": "paragraph",
                    "content": [{
                        "type": "text",
                        "text": f"{indent}{seccion['titulo']}"
                    }]
                }]
            })

        content_nodes.append({
            "type": "orderedList",
            "content": list_items
        })

        content_nodes.append({
            "type": "paragraph",
            "content": []
        })

        logger.info(f"✓ Tabla de contenidos renderizada: {len(secciones)} items")

        return {
            "type": "doc",
            "content": content_nodes
        }

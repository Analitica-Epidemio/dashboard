from typing import Any


def crear_template_seccion_evento() -> dict[str, Any]:
    """
    Crea el template de sección de evento.

    Este template se repite para CADA evento seleccionado.
    Incluye múltiples bloques dinámicos para diferentes análisis:

    1. Título y descripción del evento
    2. Texto de tendencia (auto-generado)
    3. Corredor endémico anual (52 semanas) - incluye comparación con años anteriores
    4. Análisis del período seleccionado
    5. Distribución por edad
    6. Distribución geográfica (mapa de Chubut)

    Nota: El corredor endémico ya incluye comparación temporal con los últimos 5 años
    mediante las zonas de éxito/seguridad/alerta/brote (percentiles históricos).

    Variables disponibles:
    - nombre_evento_sanitario: Nombre del evento
    - codigo_evento_snvs: Código SNVS
    - descripcion_tendencia_casos: Texto descriptivo de tendencia
    - casos_semana_actual: Casos en semana actual
    - casos_semana_anterior: Casos en semana anterior
    - porcentaje_cambio: % de cambio
    - tendencia_tipo: aumento/descenso/estable
    """
    return {
        "type": "doc",
        "content": [
            # ═══════════════════════════════════════════════════════════════════
            # TÍTULO DEL EVENTO
            # ═══════════════════════════════════════════════════════════════════
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [
                    {
                        "type": "variableNode",
                        "attrs": {"variableKey": "nombre_evento_sanitario"},
                    },
                    {"type": "text", "text": " ("},
                    {
                        "type": "variableNode",
                        "attrs": {"variableKey": "codigo_evento_snvs"},
                    },
                    {"type": "text", "text": ")"},
                ],
            },
            # ═══════════════════════════════════════════════════════════════════
            # RESUMEN DE TENDENCIA (texto auto-generado)
            # ═══════════════════════════════════════════════════════════════════
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "marks": [{"type": "bold"}],
                        "text": "Situación actual: ",
                    },
                    {"type": "text", "text": "En la semana epidemiológica "},
                    {
                        "type": "variableNode",
                        "attrs": {"variableKey": "semana_epidemiologica_actual"},
                    },
                    {"type": "text", "text": " se registraron "},
                    {
                        "type": "variableNode",
                        "attrs": {"variableKey": "casos_semana_actual"},
                    },
                    {"type": "text", "text": " casos. "},
                    {
                        "type": "variableNode",
                        "attrs": {"variableKey": "descripcion_tendencia_casos"},
                    },
                ],
            },
            # ═══════════════════════════════════════════════════════════════════
            # CORREDOR ENDÉMICO ANUAL (52 semanas)
            # ═══════════════════════════════════════════════════════════════════
            {
                "type": "heading",
                "attrs": {"level": 3},
                "content": [{"type": "text", "text": "Corredor Endémico Anual"}],
            },
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "El corredor endémico muestra la distribución esperada de casos a lo largo del año, comparando con datos históricos de los últimos 5 años.",
                    }
                ],
            },
            {
                "type": "dynamicBlock",
                "attrs": {
                    "blockId": "corredor_endemico_anual_{{ evento_codigo }}",
                    "queryType": "corredor_endemico_chart",
                    "renderType": "chart",
                    "queryParams": {
                        "periodo": "anual",
                        "anio": "{{ anio_epidemiologico }}",
                        "incluir_zonas": True,
                    },
                    "config": {
                        "titulo": "Corredor Endémico {{ nombre_evento_sanitario }} - Año {{ anio_epidemiologico }}",
                        "height": 400,
                        "mostrar_zonas": True,
                    },
                },
            },
            # ═══════════════════════════════════════════════════════════════════
            # ANÁLISIS DEL PERÍODO SELECCIONADO
            # ═══════════════════════════════════════════════════════════════════
            {
                "type": "heading",
                "attrs": {"level": 3},
                "content": [{"type": "text", "text": "Análisis del Período"}],
            },
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Detalle de las últimas "},
                    {
                        "type": "variableNode",
                        "attrs": {"variableKey": "num_semanas_analizadas"},
                    },
                    {"type": "text", "text": " semanas epidemiológicas (SE "},
                    {
                        "type": "variableNode",
                        "attrs": {"variableKey": "semana_epidemiologica_inicio"},
                    },
                    {"type": "text", "text": " a SE "},
                    {
                        "type": "variableNode",
                        "attrs": {"variableKey": "semana_epidemiologica_actual"},
                    },
                    {"type": "text", "text": "):"},
                ],
            },
            {
                "type": "dynamicBlock",
                "attrs": {
                    "blockId": "curva_epidemiologica_periodo_{{ evento_codigo }}",
                    "queryType": "curva_epidemiologica",
                    "renderType": "chart",
                    "queryParams": {},
                    "config": {
                        "titulo": "Casos por Semana - {{ nombre_evento_sanitario }}",
                        "height": 350,
                    },
                },
            },
            # ═══════════════════════════════════════════════════════════════════
            # DISTRIBUCIÓN POR EDAD (con insight auto-generado)
            # ═══════════════════════════════════════════════════════════════════
            {
                "type": "heading",
                "attrs": {"level": 3},
                "content": [{"type": "text", "text": "Distribución por Grupo Etario"}],
            },
            # Insight auto-generado sobre distribución por edad
            {
                "type": "dynamicBlock",
                "attrs": {
                    "blockId": "insight_edad_{{ evento_codigo }}",
                    "queryType": "insight_distribucion_edad",
                    "renderType": "insight_text",
                    "queryParams": {},
                    "config": {},
                },
            },
            # Gráfico de distribución por edad
            {
                "type": "dynamicBlock",
                "attrs": {
                    "blockId": "distribucion_edad_{{ evento_codigo }}",
                    "queryType": "distribucion_edad",
                    "renderType": "chart",
                    "queryParams": {},
                    "config": {
                        "titulo": "Casos por Grupo Etario - {{ nombre_evento_sanitario }}",
                        "height": 300,
                    },
                },
            },
            # ═══════════════════════════════════════════════════════════════════
            # DISTRIBUCIÓN GEOGRÁFICA (con insight auto-generado)
            # ═══════════════════════════════════════════════════════════════════
            {
                "type": "heading",
                "attrs": {"level": 3},
                "content": [{"type": "text", "text": "Distribución Geográfica"}],
            },
            # Insight auto-generado sobre distribución geográfica
            {
                "type": "dynamicBlock",
                "attrs": {
                    "blockId": "insight_geo_{{ evento_codigo }}",
                    "queryType": "insight_distribucion_geografica",
                    "renderType": "insight_text",
                    "queryParams": {},
                    "config": {},
                },
            },
            # Gráfico de distribución geográfica
            {
                "type": "dynamicBlock",
                "attrs": {
                    "blockId": "distribucion_geografica_{{ evento_codigo }}",
                    "queryType": "distribucion_geografica",
                    "renderType": "chart",
                    "queryParams": {},
                    "config": {
                        "titulo": "Casos por Departamento - {{ nombre_evento_sanitario }}",
                        "height": 350,
                    },
                },
            },
            # Separador entre eventos
            {"type": "horizontalRule"},
        ],
    }

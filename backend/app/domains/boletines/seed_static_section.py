"""
Template estatico del boletin epidemiologico.

Basado EXACTAMENTE en el Boletin Epidemiologico Semanal de Chubut SE 40 2025.

Estructura del documento de referencia:
1. Portada
2. Intro/Nota
3. Indice
4. Autoridades y Autoria
5. Tabla N°1: ENOs mas frecuentes
6. Vigilancia de IRAs:
   - Grafico N°1: Corredor endemico ETI
   - Grafico N°2: Corredor endemico Neumonia
7. Bronquiolitis:
   - Grafico N°3: Corredor endemico Bronquiolitis
   - Grafico N°4: ETI, Neumonia y Bronquiolitis por grupo etario
8. Vigilancia de Virus Respiratorios:
   - Grafico N°5: Internados por IRA segun agente viral por SE
   - Grafico N°6: Internados por IRA segun agente viral por grupo etario
   - Tablas de internaciones por hospital
9. Intoxicacion por CO:
   - Grafico N°7: Casos por UGD
10. Vigilancia de Diarreas:
    - Grafico N°8: Corredor endemico Diarrea
    - Grafico N°9: Agentes etiologicos en Diarreas por SE
11. SUH:
    - Grafico N°10: Distribucion por año
    - Tabla de casos
12. Anexos
13. Metodologia
14. Material de consulta

IMPORTANTE: Los labels de series deben coincidir EXACTAMENTE con el PDF:
- "Enfermedad tipo influenza (ETI)" - NO solo "ETI"
- "Bronquiolitis"
- "Neumonia"
- Agentes respiratorios: "VSR", "Metaneumovirus", "Influenza A", "Adenovirus", "SARS-CoV-2"
- Agentes entericos: "Rotavirus (DV)", "Salmonella spp.", "Shigella flexneri", etc.

ESTRUCTURA DE SERIES:
Cada serie en "config.series" tiene:
- label: El texto que se muestra en la leyenda (debe coincidir con el PDF)
- color: Color hex para la serie
- valores: Array de códigos que se SUMAN para esta serie
          Se interpreta según "agrupar_por" del queryParams:
          - agrupar_por="evento" -> valores son tipo_eno_codigos
          - agrupar_por="agente" -> valores son agente_codigos

Ejemplo: Para mostrar "Influenza A" como una sola serie que agrupa
         subtipos H1N1 y H3N2:
         {"label": "Influenza A", "color": "#F44336", "valores": ["influenza-a-h1n1", "influenza-a-h3n2"]}
"""

from typing import Any


def crear_template_contenido_estatico() -> dict[str, Any]:
    """
    Crea el template de contenido estatico del boletin.

    Replica EXACTAMENTE la estructura del Boletin Epi Chubut SE 40 2025.
    """
    return {
        "type": "doc",
        "content": [
            # =================================================================
            # 1. PORTADA
            # =================================================================
            {
                "type": "heading",
                "attrs": {"level": 1},
                "content": [{"type": "text", "text": "Boletín Epidemiológico Semanal"}],
            },
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Provincia del Chubut - Año "},
                    {
                        "type": "variableNode",
                        "attrs": {"variableKey": "anio_epidemiologico"},
                    },
                ],
            },
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Semana Epidemiológica "},
                    {
                        "type": "variableNode",
                        "attrs": {"variableKey": "semana_epidemiologica_actual"},
                    },
                    {"type": "text", "text": " ("},
                    {
                        "type": "variableNode",
                        "attrs": {"variableKey": "fecha_inicio_semana_epidemiologica"},
                    },
                    {"type": "text", "text": " al "},
                    {
                        "type": "variableNode",
                        "attrs": {"variableKey": "fecha_fin_semana_epidemiologica"},
                    },
                    {"type": "text", "text": ")"},
                ],
            },
            {"type": "horizontalRule"},
            # =================================================================
            # 4. TABLA N°1: ENOs MAS FRECUENTES
            # =================================================================
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [
                    {
                        "type": "text",
                        "text": "CasoEpidemiologicos de Notificación Obligatoria (ENOs)",
                    }
                ],
            },
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "Tabla N°1. Casos confirmados notificados en SNVS 2.0 más frecuentes en residentes de la Provincia de Chubut en las últimas cuatro semanas.",
                    }
                ],
            },
            {
                "type": "dynamicBlock",
                "attrs": {
                    "blockId": "tabla_enos_frecuentes",
                    "blockType": "top_enos",
                    "queryType": "top_enos",
                    "renderType": "table",
                    "queryParams": {"limit": 10},
                    "config": {
                        "titulo": "Tabla N°1. Casos confirmados notificados - ENOs más frecuentes",
                    },
                },
            },
            {"type": "horizontalRule"},
            # =================================================================
            # 5-6. VIGILANCIA DE INFECCIONES RESPIRATORIAS AGUDAS
            # =================================================================
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [
                    {
                        "type": "text",
                        "text": "Vigilancia de Infecciones Respiratorias Agudas",
                    }
                ],
            },
            # -----------------------------------------------------------------
            # ENFERMEDAD TIPO INFLUENZA (ETI) - Grafico N°1
            # -----------------------------------------------------------------
            {
                "type": "heading",
                "attrs": {"level": 3},
                "content": [
                    {"type": "text", "text": "Enfermedad Tipo Influenza (ETI)"}
                ],
            },
            {
                "type": "dynamicBlock",
                "attrs": {
                    "blockId": "corredor_eti",
                    "blockType": "corredor_evento_especifico",
                    "queryType": "corredor_endemico_chart",
                    "renderType": "chart",
                    "queryParams": {
                        "evento_codigo": "eti",
                        "periodo": "anual",
                    },
                    "config": {
                        "titulo": "Gráfico N°1. Corredor endémico semanal de ETI",
                        "height": 400,
                        "mostrar_zonas": True,
                    },
                },
            },
            # -----------------------------------------------------------------
            # NEUMONIA - Grafico N°2
            # -----------------------------------------------------------------
            {
                "type": "heading",
                "attrs": {"level": 3},
                "content": [{"type": "text", "text": "Neumonía"}],
            },
            {
                "type": "dynamicBlock",
                "attrs": {
                    "blockId": "corredor_neumonia",
                    "blockType": "corredor_evento_especifico",
                    "queryType": "corredor_endemico_chart",
                    "renderType": "chart",
                    "queryParams": {
                        "evento_codigo": "neumonia",
                        "periodo": "anual",
                    },
                    "config": {
                        "titulo": "Gráfico N°2. Corredor endémico semanal de Neumonía",
                        "height": 400,
                        "mostrar_zonas": True,
                    },
                },
            },
            {"type": "horizontalRule"},
            # =================================================================
            # 7. BRONQUIOLITIS
            # =================================================================
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{"type": "text", "text": "Bronquiolitis"}],
            },
            # -----------------------------------------------------------------
            # Grafico N°3: Corredor endemico Bronquiolitis
            # -----------------------------------------------------------------
            {
                "type": "dynamicBlock",
                "attrs": {
                    "blockId": "corredor_bronquiolitis",
                    "blockType": "corredor_evento_especifico",
                    "queryType": "corredor_endemico_chart",
                    "renderType": "chart",
                    "queryParams": {
                        "evento_codigo": "bronquiolitis",
                        "periodo": "anual",
                    },
                    "config": {
                        "titulo": "Gráfico N°3. Corredor endémico semanal de Bronquiolitis",
                        "height": 400,
                        "mostrar_zonas": True,
                    },
                },
            },
            # -----------------------------------------------------------------
            # Grafico N°4: ETI, Neumonia y Bronquiolitis por grupo etario
            # LABELS EXACTOS del PDF: "Bronquiolitis", "Enfermedad tipo influenza (ETI)", "Neumonia"
            # -----------------------------------------------------------------
            {
                "type": "dynamicBlock",
                "attrs": {
                    "blockId": "ira_eventos_por_edad",
                    "blockType": "edad_comparar_eventos",
                    "queryType": "distribucion_edad",
                    "renderType": "chart",
                    "queryParams": {
                        "eventos_codigos": ["bronquiolitis", "eti", "neumonia"],
                        "agrupar_por": "evento",
                        "periodo": "anual",  # Casos de todo el año
                    },
                    "config": {
                        "titulo": "Gráfico N°4. Casos de ETI, Neumonía y Bronquiolitis por grupo etario",
                        "height": 400,
                        "chart_type": "stacked_bar",
                        "show_legend": True,
                        # Cada serie puede agrupar múltiples códigos bajo un label
                        # "valores" se interpreta según "agrupar_por" del queryParams
                        "series": [
                            {
                                "label": "Bronquiolitis",
                                "color": "#F44336",
                                "valores": ["bronquiolitis"],
                            },
                            {
                                "label": "Enfermedad tipo influenza (ETI)",
                                "color": "#2196F3",
                                "valores": ["eti"],
                            },
                            {
                                "label": "Neumonía",
                                "color": "#FF9800",
                                "valores": ["neumonia"],
                            },
                        ],
                    },
                },
            },
            {"type": "horizontalRule"},
            # =================================================================
            # 8. VIGILANCIA DE VIRUS RESPIRATORIOS EN INTERNADOS
            # =================================================================
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [
                    {
                        "type": "text",
                        "text": "Vigilancia de Virus Respiratorios en Internados y/o Fallecidos por IRA",
                    }
                ],
            },
            # -----------------------------------------------------------------
            # Grafico N°5: Internados por IRA segun agente viral por SE
            # LABELS EXACTOS: VSR, Metaneumovirus, Influenza A, Adenovirus, SARS-CoV-2
            # -----------------------------------------------------------------
            {
                "type": "dynamicBlock",
                "attrs": {
                    "blockId": "internados_ira_agente_semana",
                    "blockType": "curva_por_agente",
                    "queryType": "curva_epidemiologica",
                    "renderType": "chart",
                    "queryParams": {
                        "evento_codigo": "uc-irag",
                        "solo_internados": True,
                        "resultado": "positivo",
                        "agentes_codigos": [
                            "vsr",
                            "metapneumovirus",
                            "influenza-a",
                            "adenovirus",
                            "sars-cov-2",
                        ],
                        "agrupar_por": "agente",
                        "periodo": "anual",  # Tendencia de todo el año
                    },
                    "config": {
                        "titulo": "Gráfico N°5. Casos de internados por IRA según agente viral detectado por semana epidemiológica",
                        "height": 400,
                        "chart_type": "stacked_bar",
                        "show_legend": True,
                        # "valores" son agente_codigos porque agrupar_por="agente"
                        # Permite agrupar múltiples agentes bajo un label (ej: influenza-a-h1n1 + h3n2 = "Influenza A")
                        "series": [
                            {"label": "VSR", "color": "#2196F3", "valores": ["vsr"]},
                            {
                                "label": "Metaneumovirus",
                                "color": "#9C27B0",
                                "valores": ["metaneumovirus"],
                            },
                            {
                                "label": "Influenza A",
                                "color": "#F44336",
                                "valores": ["influenza-a"],
                            },
                            {
                                "label": "Adenovirus",
                                "color": "#4CAF50",
                                "valores": ["adenovirus-respiratorio"],
                            },
                            {
                                "label": "SARS-CoV-2",
                                "color": "#FF9800",
                                "valores": ["sars-cov-2"],
                            },
                        ],
                    },
                },
            },
            # -----------------------------------------------------------------
            # Grafico N°6: Internados por IRA segun agente viral por grupo etario
            # -----------------------------------------------------------------
            {
                "type": "dynamicBlock",
                "attrs": {
                    "blockId": "internados_ira_agente_edad",
                    "blockType": "edad_por_agente",
                    "queryType": "distribucion_edad",
                    "renderType": "chart",
                    "queryParams": {
                        "evento_codigo": "uc-irag",
                        "solo_internados": True,
                        "resultado": "positivo",
                        "agentes_codigos": [
                            "vsr",
                            "metapneumovirus",
                            "influenza-a",
                            "adenovirus",
                            "sars-cov-2",
                        ],
                        "agrupar_por": "agente",
                        "periodo": "anual",  # Casos de todo el año
                    },
                    "config": {
                        "titulo": "Gráfico N°6. Casos de internado por IRA según agente viral detectado por grupos de edad",
                        "height": 400,
                        "chart_type": "stacked_bar",
                        "show_legend": True,
                        "series": [
                            {
                                "label": "SARS-CoV-2",
                                "color": "#FF9800",
                                "valores": ["sars-cov-2"],
                            },
                            {
                                "label": "Adenovirus",
                                "color": "#4CAF50",
                                "valores": ["adenovirus-respiratorio"],
                            },
                            {
                                "label": "Influenza A",
                                "color": "#F44336",
                                "valores": ["influenza-a"],
                            },
                            {
                                "label": "Metaneumovirus",
                                "color": "#9C27B0",
                                "valores": ["metaneumovirus"],
                            },
                            {"label": "VSR", "color": "#2196F3", "valores": ["vsr"]},
                        ],
                    },
                },
            },
            {"type": "horizontalRule"},
            # =================================================================
            # 9. INTOXICACION POR MONOXIDO DE CARBONO (CO)
            # =================================================================
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [
                    {
                        "type": "text",
                        "text": "Intoxicación por Monóxido de Carbono (CO)",
                    }
                ],
            },
            # -----------------------------------------------------------------
            # Grafico N°7: Casos por UGD comparando años
            # -----------------------------------------------------------------
            {
                "type": "dynamicBlock",
                "attrs": {
                    "blockId": "intoxicacion_co_ugd",
                    "blockType": "comparacion_periodos_global",
                    "queryType": "comparacion_anual",
                    "renderType": "chart",
                    "queryParams": {
                        "evento_codigo": "intoxicacion-co",
                    },
                    "config": {
                        "titulo": "Gráfico N°7. Casos confirmados de intoxicación por monóxido de carbono",
                        "height": 400,
                    },
                },
            },
            {"type": "horizontalRule"},
            # =================================================================
            # 10. VIGILANCIA DE DIARREAS
            # =================================================================
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{"type": "text", "text": "Vigilancia de Diarrea"}],
            },
            # -----------------------------------------------------------------
            # Grafico N°8: Corredor endemico Diarrea
            # -----------------------------------------------------------------
            {
                "type": "dynamicBlock",
                "attrs": {
                    "blockId": "corredor_diarrea",
                    "blockType": "corredor_evento_especifico",
                    "queryType": "corredor_endemico_chart",
                    "renderType": "chart",
                    "queryParams": {
                        "evento_codigo": "diarrea-aguda",
                        "periodo": "anual",
                    },
                    "config": {
                        "titulo": "Gráfico N°8. Corredor endémico semanal de Diarrea",
                        "height": 400,
                        "mostrar_zonas": True,
                    },
                },
            },
            # -----------------------------------------------------------------
            # Grafico N°9: Agentes etiologicos en Diarreas por SE
            # LABELS EXACTOS: Rotavirus (DV), Salmonella spp., Shigella flexneri,
            #                 Shigella sonnei, Shigella spp., STEC O157, Adenovirus (DV)
            # -----------------------------------------------------------------
            {
                "type": "heading",
                "attrs": {"level": 3},
                "content": [
                    {
                        "type": "text",
                        "text": "Casos de Diarrea Aguda según Agente Etiológico",
                    }
                ],
            },
            {
                "type": "dynamicBlock",
                "attrs": {
                    "blockId": "agentes_diarreas_semana",
                    "blockType": "curva_por_agente",
                    "queryType": "curva_epidemiologica",
                    "renderType": "chart",
                    "queryParams": {
                        "eventos_codigos": ["diarrea-aguda", "suh"],
                        "resultado": "positivo",
                        "agentes_codigos": [
                            "rotavirus",
                            "salmonella-spp",
                            "shigella-flexneri",
                            "shigella-sonnei",
                            "shigella-spp",
                            "stec-o157",
                            "adenovirus-enterico",
                        ],
                        "agrupar_por": "agente",
                        "periodo": "anual",  # Tendencia de todo el año
                    },
                    "config": {
                        "titulo": "Gráfico N°9. Distribución de agentes etiológicos en Diarreas Agudas según semana epidemiológica",
                        "height": 400,
                        "chart_type": "stacked_bar",
                        "show_legend": True,
                        "series": [
                            {
                                "label": "Rotavirus (DV)",
                                "color": "#2196F3",
                                "valores": ["rotavirus"],
                            },
                            {
                                "label": "Salmonella spp.",
                                "color": "#FF9800",
                                "valores": ["salmonella-spp"],
                            },
                            {
                                "label": "Shigella flexneri",
                                "color": "#9C27B0",
                                "valores": ["shigella-flexneri"],
                            },
                            {
                                "label": "Shigella sonnei",
                                "color": "#F44336",
                                "valores": ["shigella-sonnei"],
                            },
                            {
                                "label": "Shigella spp.",
                                "color": "#E91E63",
                                "valores": ["shigella-spp"],
                            },
                            {
                                "label": "STEC O157",
                                "color": "#795548",
                                "valores": ["stec-o157"],
                            },
                            {
                                "label": "Adenovirus (DV)",
                                "color": "#4CAF50",
                                "valores": ["adenovirus-enterico"],
                            },
                        ],
                    },
                },
            },
            {"type": "horizontalRule"},
            # =================================================================
            # 11. SINDROME UREMICO HEMOLITICO (SUH)
            # =================================================================
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [
                    {"type": "text", "text": "Síndrome Urémico Hemolítico (SUH)"}
                ],
            },
            # -----------------------------------------------------------------
            # Grafico N°10: Distribucion de casos por año
            # -----------------------------------------------------------------
            {
                "type": "dynamicBlock",
                "attrs": {
                    "blockId": "suh_distribucion_anual",
                    "blockType": "comparacion_periodos_global",
                    "queryType": "comparacion_anual",
                    "renderType": "chart",
                    "queryParams": {
                        "evento_codigo": "suh",
                    },
                    "config": {
                        "titulo": "Gráfico N°10. Distribución de Casos de SUH según año de consulta",
                        "height": 400,
                    },
                },
            },
            # -----------------------------------------------------------------
            # Corredor endemico SUH
            # -----------------------------------------------------------------
            {
                "type": "dynamicBlock",
                "attrs": {
                    "blockId": "corredor_suh",
                    "blockType": "corredor_evento_especifico",
                    "queryType": "corredor_endemico_chart",
                    "renderType": "chart",
                    "queryParams": {
                        "evento_codigo": "suh",
                        "periodo": "anual",
                    },
                    "config": {
                        "titulo": "Corredor Endémico SUH",
                        "height": 400,
                        "mostrar_zonas": True,
                    },
                },
            },
            {"type": "horizontalRule"},
            # =================================================================
            # PLACEHOLDER PARA EVENTOS SELECCIONADOS (LOOP DE EVENTOS)
            # Este es el unico agregado respecto al PDF de referencia
            # =================================================================
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [
                    {
                        "type": "text",
                        "text": "Análisis por CasoEpidemiologico Seleccionado",
                    }
                ],
            },
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "marks": [{"type": "italic"}],
                        "text": "(Las siguientes secciones se generan dinámicamente para cada evento seleccionado)",
                    }
                ],
            },
            {
                "type": "selectedEventsPlaceholder",
                "attrs": {},
            },
            {"type": "horizontalRule"},
            # =================================================================
            # 12. ANEXOS
            # =================================================================
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{"type": "text", "text": "Anexo"}],
            },
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "Anexo N°1: Calendario Epidemiológico",
                    }
                ],
            },
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "Anexo N°2: Flujograma Síndrome Urémico Hemolítico",
                    }
                ],
            },
            {"type": "horizontalRule"},
            # =================================================================
            # 13. METODOLOGIA
            # =================================================================
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{"type": "text", "text": "Metodología Utilizada"}],
            },
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "Fuente: SNVS2.0 - SISA",
                    }
                ],
            },
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "Los datos provienen del Sistema Nacional de Vigilancia de la Salud (SNVS 2.0). "
                        "Se consideran casos notificados según clasificación del evento. "
                        "Para la construcción de los corredores endémicos, se utilizan los años 2018, 2019, 2022, 2023 y 2024 "
                        "(excluyendo los años de pandemia de COVID-19).",
                    }
                ],
            },
            {"type": "horizontalRule"},
            # =================================================================
            # 14. MATERIAL DE CONSULTA
            # =================================================================
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{"type": "text", "text": "Material de Consulta"}],
            },
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "• Manual de normas y procedimientos de vigilancia y control de eventos de notificación obligatoria - Ministerio de Salud de la Nación",
                    }
                ],
            },
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "• Boletín Epidemiológico Nacional - Dirección de Epidemiología",
                    }
                ],
            },
        ],
    }

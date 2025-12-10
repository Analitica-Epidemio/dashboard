"""
Seed de secciones y bloques para el sistema de boletines v2.

Basado en el Boletín Epidemiológico Semanal de Chubut SE 40 2025.
Ver /docs/BOLETIN_ESTRUCTURA.md para estructura detallada.

MAPEO DE DATOS:
===============
1. CLI_P26 (casos clínicos ambulatorios):
   - Corredor endémico de ETI (nombre: contiene "ETI" o "Influenza")
   - Corredor endémico de Neumonía (nombre: contiene "Neumon")
   - Corredor endémico de Bronquiolitis (nombre: contiene "Bronquiolitis")
   - Corredor endémico de Diarrea (nombre: contiene "Diarrea")
   - Distribución por grupo etario

2. LAB_P26 (estudios de laboratorio):
   - Virus respiratorios por semana (agrupacion:respiratorio)
   - Virus respiratorios por edad (agrupacion:respiratorio)
   - Agentes entéricos por semana (agrupacion:enterico)

3. CLI_P26_INT (internaciones IRA):
   - Ocupación de camas IRA/UTI/ARM por hospital

4. NOMINAL (casos nominales):
   - ENOs más frecuentes
   - Intoxicación por CO
   - SUH (serie histórica + tabla de casos)

SLUGS GENERADOS AUTOMÁTICAMENTE:
================================
Los slugs de TipoCasoEpidemiologicoPasivo se generan desde NOMBREEVENTOAGRP:
- "ETI" → "eti"
- "Neumonía" → "neumonia"
- "Bronquiolitis" → "bronquiolitis"
- "Diarreas sin especificar" → "diarreas-sin-especificar"
"""

from sqlmodel import Session, select

from app.domains.boletines.constants import TipoBloque, TipoVisualizacion
from app.domains.boletines.models import BoletinBloque, BoletinSeccion


def seed_secciones_y_bloques(session: Session) -> None:
    """
    Crea las secciones y bloques del boletín epidemiológico.

    Usa upsert (insert or update on conflict) para ser idempotente.
    """
    secciones = _crear_secciones()
    bloques = _crear_bloques()

    # Insertar secciones
    for seccion_data in secciones:
        stmt = select(BoletinSeccion).where(BoletinSeccion.slug == seccion_data["slug"])
        existing = session.execute(stmt).scalar_one_or_none()

        if existing:
            for key, value in seccion_data.items():
                setattr(existing, key, value)
        else:
            seccion = BoletinSeccion(**seccion_data)
            session.add(seccion)

    session.commit()

    # Obtener IDs de secciones para los bloques
    seccion_ids = {}
    for seccion_data in secciones:
        stmt = select(BoletinSeccion).where(BoletinSeccion.slug == seccion_data["slug"])
        seccion = session.execute(stmt).scalar_one()
        seccion_ids[seccion_data["slug"]] = seccion.id

    # Insertar bloques
    for bloque_data in bloques:
        seccion_slug = bloque_data.pop("seccion_slug")
        bloque_data["seccion_id"] = seccion_ids[seccion_slug]

        stmt = select(BoletinBloque).where(BoletinBloque.slug == bloque_data["slug"])
        existing = session.execute(stmt).scalar_one_or_none()

        if existing:
            for key, value in bloque_data.items():
                setattr(existing, key, value)
        else:
            bloque = BoletinBloque(**bloque_data)
            session.add(bloque)

    session.commit()


def _crear_secciones() -> list[dict]:
    """Define las secciones del boletín."""
    return [
        {
            "slug": "enos-frecuentes",
            "titulo": "Eventos de Notificación Obligatoria (ENOs)",
            "orden": 1,
            "activo": True,
            "descripcion": "Tabla de ENOs más frecuentes - datos nominales",
        },
        {
            "slug": "ira",
            "titulo": "Vigilancia de Infecciones Respiratorias Agudas",
            "orden": 2,
            "activo": True,
            "descripcion": "ETI, Neumonía desde CLI_P26",
        },
        {
            "slug": "bronquiolitis",
            "titulo": "Bronquiolitis",
            "orden": 3,
            "activo": True,
            "descripcion": "Corredor y distribución por edad - CLI_P26",
        },
        {
            "slug": "virus-respiratorios",
            "titulo": "Vigilancia de Virus Respiratorios en Internados y/o Fallecidos por IRA",
            "orden": 4,
            "activo": True,
            "descripcion": "Agentes virales en internados - NOMINAL (NOM_P26_VR)",
        },
        {
            "slug": "hospitalizacion",
            "titulo": "Ocupación Hospitalaria por IRA",
            "orden": 5,
            "activo": True,
            "descripcion": "Camas UTI/ARM por IRA - CLI_P26_INT",
        },
        {
            "slug": "co",
            "titulo": "Intoxicación por Monóxido de Carbono (CO)",
            "orden": 6,
            "activo": True,
            "descripcion": "Casos de CO - NOMINAL",
        },
        {
            "slug": "diarreas",
            "titulo": "Vigilancia de Diarrea",
            "orden": 7,
            "activo": True,
            "descripcion": "Corredor de diarrea (CLI_P26) y agentes (LAB_P26)",
        },
        {
            "slug": "suh",
            "titulo": "Síndrome Urémico Hemolítico (SUH)",
            "orden": 8,
            "activo": True,
            "descripcion": "Casos de SUH - NOMINAL",
        },
    ]


def _crear_bloques() -> list[dict]:
    """Define los bloques de cada sección."""
    return [
        # ═══════════════════════════════════════════════════════════════
        # SECCIÓN: ENOs FRECUENTES
        # ═══════════════════════════════════════════════════════════════
        {
            "seccion_slug": "enos-frecuentes",
            "slug": "tabla-top-enos",
            "titulo_template": "Tabla N°1. Casos confirmados notificados en SNVS 2.0 más frecuentes",
            "tipo_bloque": TipoBloque.TOP_EVENTOS,
            "tipo_visualizacion": TipoVisualizacion.TABLE,
            "metrica_codigo": "casos_nominales",
            "dimensiones": ["TIPO_ENO"],
            "criterios_fijos": {},
            "series_source": None,
            "series_config": None,
            "config_visual": {"limit": 10, "show_comparison": True},
            "orden": 1,
            "activo": True,
        },
        # ═══════════════════════════════════════════════════════════════
        # SECCIÓN: IRA (ETI, Neumonía)
        # ═══════════════════════════════════════════════════════════════
        {
            "seccion_slug": "ira",
            "slug": "corredor-eti",
            "titulo_template": "Gráfico N°1. Corredor endémico semanal de Enfermedad Tipo Influenza (ETI). Provincia del Chubut. SE 1-{{ semana }} Año {{ anio }}",
            "tipo_bloque": TipoBloque.CORREDOR_ENDEMICO,
            "tipo_visualizacion": TipoVisualizacion.AREA_CHART,
            "metrica_codigo": "casos_clinicos",
            "dimensiones": ["SEMANA_EPIDEMIOLOGICA", "ANIO_EPIDEMIOLOGICO"],
            "compute": "corredor_endemico",
            # Usa tipo_evento_nombre con ilike para buscar por nombre parcial
            "criterios_fijos": {"tipo_evento_nombre": "ETI"},
            "series_source": None,
            "series_config": [{"slug": "eti", "label": "ETI", "color": "#2196F3"}],
            "config_visual": {
                "height": 400,
                "mostrar_zonas": True,
                "zonas": [
                    {"key": "exito", "color": "#4CAF50", "label": "Éxito"},
                    {"key": "seguridad", "color": "#FFEB3B", "label": "Seguridad"},
                    {"key": "alerta", "color": "#FF9800", "label": "Alerta"},
                    {"key": "brote", "color": "#F44336", "label": "Brote"},
                ],
            },
            "orden": 1,
            "activo": True,
        },
        {
            "seccion_slug": "ira",
            "slug": "corredor-neumonia",
            "titulo_template": "Gráfico N°2. Corredor endémico semanal de Neumonía. Provincia del Chubut. SE 1-{{ semana }} Año {{ anio }}",
            "tipo_bloque": TipoBloque.CORREDOR_ENDEMICO,
            "tipo_visualizacion": TipoVisualizacion.AREA_CHART,
            "metrica_codigo": "casos_clinicos",
            "dimensiones": ["SEMANA_EPIDEMIOLOGICA", "ANIO_EPIDEMIOLOGICO"],
            "compute": "corredor_endemico",
            "criterios_fijos": {"tipo_evento_nombre": "Neumon"},
            "series_source": None,
            "series_config": [
                {"slug": "neumonia", "label": "Neumonía", "color": "#FF9800"}
            ],
            "config_visual": {
                "height": 400,
                "mostrar_zonas": True,
                "zonas": [
                    {"key": "exito", "color": "#4CAF50", "label": "Éxito"},
                    {"key": "seguridad", "color": "#FFEB3B", "label": "Seguridad"},
                    {"key": "alerta", "color": "#FF9800", "label": "Alerta"},
                    {"key": "brote", "color": "#F44336", "label": "Brote"},
                ],
            },
            "orden": 2,
            "activo": True,
        },
        # ═══════════════════════════════════════════════════════════════
        # SECCIÓN: BRONQUIOLITIS
        # ═══════════════════════════════════════════════════════════════
        {
            "seccion_slug": "bronquiolitis",
            "slug": "corredor-bronquiolitis",
            "titulo_template": "Gráfico N°3. Corredor endémico semanal de Bronquiolitis. Provincia del Chubut. SE 1-{{ semana }}. Año {{ anio }}",
            "tipo_bloque": TipoBloque.CORREDOR_ENDEMICO,
            "tipo_visualizacion": TipoVisualizacion.AREA_CHART,
            "metrica_codigo": "casos_clinicos",
            "dimensiones": ["SEMANA_EPIDEMIOLOGICA", "ANIO_EPIDEMIOLOGICO"],
            "compute": "corredor_endemico",
            "criterios_fijos": {"tipo_evento_nombre": "Bronquiolitis"},
            "series_source": None,
            "series_config": [
                {"slug": "bronquiolitis", "label": "Bronquiolitis", "color": "#F44336"}
            ],
            "config_visual": {
                "height": 400,
                "mostrar_zonas": True,
                "zonas": [
                    {"key": "exito", "color": "#4CAF50", "label": "Éxito"},
                    {"key": "seguridad", "color": "#FFEB3B", "label": "Seguridad"},
                    {"key": "alerta", "color": "#FF9800", "label": "Alerta"},
                    {"key": "brote", "color": "#F44336", "label": "Brote"},
                ],
            },
            "orden": 1,
            "activo": True,
        },
        {
            "seccion_slug": "bronquiolitis",
            "slug": "ira-por-edad",
            "titulo_template": "Gráfico N°4. Casos de ETI, Neumonía y Bronquiolitis por grupo etario. Provincia del Chubut. SE 1-{{ semana }} Año {{ anio }}",
            "tipo_bloque": TipoBloque.DISTRIBUCION_EDAD,
            "tipo_visualizacion": TipoVisualizacion.STACKED_BAR,
            "metrica_codigo": "casos_clinicos",
            "dimensiones": ["GRUPO_ETARIO", "TIPO_EVENTO"],
            "criterios_fijos": {},
            # Las series se resuelven por nombre de evento (ilike)
            "series_source": None,
            "series_config": [
                {"tipo_evento_nombre": "ETI", "label": "ETI", "color": "#2196F3"},
                {
                    "tipo_evento_nombre": "Neumon",
                    "label": "Neumonía",
                    "color": "#03A9F4",
                },
                {
                    "tipo_evento_nombre": "Bronquiolitis",
                    "label": "Bronquiolitis",
                    "color": "#F44336",
                },
            ],
            "config_visual": {
                "height": 400,
                "show_legend": True,
                # Año completo: SE 1 hasta SE actual
                "rango_temporal": "anio_completo",
                "grupos_etarios_orden": [
                    "<6 m",
                    "6 a 11 m",
                    "12 a 23 m",
                    "2 a 4",
                    "5 a 9",
                    "10 a 14",
                    "15 a 19",
                    "20 a 24",
                    "25 a 34",
                    "35 a 44",
                    "45 a 64",
                    "65 a 74",
                    ">= a 75",
                    "Edad Sin Esp.",
                ],
            },
            "orden": 2,
            "activo": True,
        },
        # ═══════════════════════════════════════════════════════════════
        # SECCIÓN: VIRUS RESPIRATORIOS EN INTERNADOS
        # Usa muestras_positivas de LAB_P26 (datos de laboratorio)
        # Según boletín: VSR, Metaneumovirus, Influenza A, Adenovirus, SARS-CoV-2
        # ═══════════════════════════════════════════════════════════════
        {
            "seccion_slug": "virus-respiratorios",
            "slug": "virus-resp-semana",
            "titulo_template": "Gráfico N°5. Casos de internados por IRA según agente viral detectado por semana epidemiológica. Provincia del Chubut. SE 1-{{ semana }}. Año {{ anio }}",
            "tipo_bloque": TipoBloque.CURVA_EPIDEMIOLOGICA,
            "tipo_visualizacion": TipoVisualizacion.STACKED_BAR,
            "metrica_codigo": "muestras_positivas",
            "dimensiones": ["SEMANA_EPIDEMIOLOGICA", "AGENTE_ETIOLOGICO"],
            # Año completo para ver tendencia completa
            "criterios_fijos": {},
            "series_source": "agrupacion:respiratorio",
            "series_config": None,
            "config_visual": {
                "height": 400,
                "show_legend": True,
                "show_values_on_bars": True,
                # Año completo: SE 1 hasta SE actual
                "rango_temporal": "anio_completo",
                "colores_agentes": {
                    "VSR": "#2196F3",
                    "Metaneumovirus": "#FFEB3B",
                    "Influenza A": "#9E9E9E",
                    "Adenovirus": "#FF9800",
                    "SARS-CoV-2": "#E91E63",
                },
            },
            "orden": 1,
            "activo": True,
        },
        {
            "seccion_slug": "virus-respiratorios",
            "slug": "virus-resp-edad",
            "titulo_template": "Gráfico N°6. Casos de internado por IRA según agente viral detectado por grupos de edad. Provincia del Chubut. SE 1-{{ semana }}. Año {{ anio }}",
            "tipo_bloque": TipoBloque.DISTRIBUCION_EDAD,
            "tipo_visualizacion": TipoVisualizacion.STACKED_BAR,
            "metrica_codigo": "muestras_positivas",
            "dimensiones": ["GRUPO_ETARIO", "AGENTE_ETIOLOGICO"],
            "criterios_fijos": {},
            "series_source": "agrupacion:respiratorio",
            "series_config": None,
            "config_visual": {
                "height": 400,
                "show_legend": True,
                # Año completo: SE 1 hasta SE actual
                "rango_temporal": "anio_completo",
                "colores_agentes": {
                    "VSR": "#2196F3",
                    "Metaneumovirus": "#FFEB3B",
                    "Influenza A": "#9E9E9E",
                    "Adenovirus": "#FF9800",
                    "SARS-CoV-2": "#E91E63",
                },
            },
            "orden": 2,
            "activo": True,
        },
        # ═══════════════════════════════════════════════════════════════
        # SECCIÓN: OCUPACIÓN HOSPITALARIA (CLI_P26_INT)
        # Tabla N°2: Dotación de camas + Tablas N°3-6: Ocupación por hospital
        # ═══════════════════════════════════════════════════════════════
        {
            "seccion_slug": "hospitalizacion",
            "slug": "dotacion-camas",
            "titulo_template": "Tabla N°2. Dotación de camas por establecimiento",
            "tipo_bloque": TipoBloque.TABLA_RESUMEN,
            "tipo_visualizacion": TipoVisualizacion.TABLE,
            "metrica_codigo": "dotacion_camas",
            "dimensiones": ["ESTABLECIMIENTO", "TIPO_CAMA"],
            "criterios_fijos": {},
            "series_source": None,
            "series_config": None,
            "config_visual": {
                "columnas": [
                    "Dotación camas internación general adultos",
                    "Dotación camas internación general pediátricas",
                    "Dotación UTI adultos",
                    "Dotación UTI pediátricas",
                ],
                "hospitales": ["HZPM", "HZTW", "HRCR", "HSRW"],
            },
            "orden": 1,
            "activo": True,
        },
        {
            "seccion_slug": "hospitalizacion",
            "slug": "ocupacion-camas-ira",
            "titulo_template": "Tablas N°3-6. Ocupación por IRA por establecimiento. SE {{ semana - 5 }} a SE {{ semana }}",
            "tipo_bloque": TipoBloque.TABLA_RESUMEN,
            "tipo_visualizacion": TipoVisualizacion.TABLE,
            "metrica_codigo": "ocupacion_camas_ira",
            "dimensiones": [
                "ESTABLECIMIENTO",
                "SEMANA_EPIDEMIOLOGICA",
                "TIPO_INTERNACION",
            ],
            "criterios_fijos": {},
            "series_source": None,
            "series_config": None,
            "config_visual": {
                # Últimas 6 semanas para tablas de ocupación
                "rango_temporal": "ultimas_6_semanas",
                "filas": [
                    "Internación general adultos por IRA",
                    "UTI por IRA adultos",
                    "Pediátricos en internación por IRA",
                    "ARM por IRA adultos",
                    "Pediátricos UTI por IRA",
                    "ARM por IRA pediátricos",
                ],
                "mostrar_porcentajes": True,
            },
            "orden": 2,
            "activo": True,
        },
        # ═══════════════════════════════════════════════════════════════
        # SECCIÓN: INTOXICACIÓN POR CO
        # ═══════════════════════════════════════════════════════════════
        {
            "seccion_slug": "co",
            "slug": "casos-co",
            "titulo_template": "Gráfico N°7. Casos confirmados de intoxicación por monóxido de carbono",
            "tipo_bloque": TipoBloque.COMPARACION_ANUAL,
            "tipo_visualizacion": TipoVisualizacion.GROUPED_BAR,
            "metrica_codigo": "casos_nominales",
            "dimensiones": ["DEPARTAMENTO", "ANIO_EPIDEMIOLOGICO"],
            "criterios_fijos": {"tipo_evento_slug": "intoxicacion-co"},
            "series_source": None,
            "series_config": [
                {"slug": "co", "label": "Intoxicación por CO", "color": "#795548"}
            ],
            "config_visual": {"height": 400},
            "orden": 1,
            "activo": True,
        },
        # ═══════════════════════════════════════════════════════════════
        # SECCIÓN: DIARREAS
        # Corredor desde CLI_P26, Agentes desde LAB_P26
        # ═══════════════════════════════════════════════════════════════
        {
            "seccion_slug": "diarreas",
            "slug": "corredor-diarrea",
            "titulo_template": "Gráfico N°8. Corredor endémico semanal de Diarrea. Provincia del Chubut. SE 1-{{ semana }} {{ anio }}",
            "tipo_bloque": TipoBloque.CORREDOR_ENDEMICO,
            "tipo_visualizacion": TipoVisualizacion.AREA_CHART,
            "metrica_codigo": "casos_clinicos",
            "dimensiones": ["SEMANA_EPIDEMIOLOGICA", "ANIO_EPIDEMIOLOGICO"],
            "compute": "corredor_endemico",
            # Buscar por nombre parcial - diarrea en cualquier variante
            "criterios_fijos": {"tipo_evento_nombre": "Diarrea"},
            "series_source": None,
            "series_config": [
                {"slug": "diarrea", "label": "Diarrea", "color": "#4CAF50"}
            ],
            "config_visual": {
                "height": 400,
                "mostrar_zonas": True,
                "zonas": [
                    {"key": "exito", "color": "#4CAF50", "label": "Éxito"},
                    {"key": "seguridad", "color": "#FFEB3B", "label": "Seguridad"},
                    {"key": "alerta", "color": "#FF9800", "label": "Alerta"},
                    {"key": "brote", "color": "#F44336", "label": "Brote"},
                ],
            },
            "orden": 1,
            "activo": True,
        },
        {
            "seccion_slug": "diarreas",
            "slug": "tabla-muestras-diarrea",
            "titulo_template": "Tabla N°7. Muestras de diarrea procesadas",
            "tipo_bloque": TipoBloque.TABLA_RESUMEN,
            "tipo_visualizacion": TipoVisualizacion.TABLE,
            "metrica_codigo": "muestras_estudiadas",
            "dimensiones": ["TIPO_MUESTRA"],
            "criterios_fijos": {},
            "series_source": None,
            "series_config": None,
            "config_visual": {
                "columnas": ["Muestras estudiadas", "Muestras positivas"],
                "filas": [
                    "Diarreas Bacterianas",
                    "Diarreas Virales – Ambulatorios",
                    "Diarreas Virales – Internados",
                ],
                "mostrar_totales": True,
            },
            "orden": 2,
            "activo": True,
        },
        {
            "seccion_slug": "diarreas",
            "slug": "agentes-diarrea-semana",
            "titulo_template": "Gráfico N°9. Distribución de agentes etiológicos en Diarreas Agudas según semana epidemiológica. Provincia del Chubut. SE 1-{{ semana }} Año {{ anio }}",
            "tipo_bloque": TipoBloque.CURVA_EPIDEMIOLOGICA,
            "tipo_visualizacion": TipoVisualizacion.STACKED_BAR,
            "metrica_codigo": "muestras_positivas",
            "dimensiones": ["SEMANA_EPIDEMIOLOGICA", "AGENTE_ETIOLOGICO"],
            "criterios_fijos": {},
            "series_source": "agrupacion:enterico",
            "series_config": None,
            "config_visual": {
                "height": 400,
                "show_legend": True,
                "colores_agentes": {
                    "Rotavirus": "#2196F3",
                    "Salmonella spp": "#FFEB3B",
                    "Shigella flexneri": "#795548",
                    "Shigella sonnei": "#FF9800",
                    "Shigella spp": "#9E9E9E",
                    "STEC O157": "#F44336",
                    "Adenovirus (DV)": "#4CAF50",
                },
            },
            "orden": 3,
            "activo": True,
        },
        # ═══════════════════════════════════════════════════════════════
        # SECCIÓN: SUH (Síndrome Urémico Hemolítico)
        # Serie histórica + Tabla descriptiva de casos confirmados
        # ═══════════════════════════════════════════════════════════════
        {
            "seccion_slug": "suh",
            "slug": "suh-serie-historica",
            "titulo_template": "Gráfico N°10. Distribución de Casos de SUH según año de consulta. Provincia del Chubut. Período 2014-SE {{ semana }} {{ anio }}",
            "tipo_bloque": TipoBloque.COMPARACION_ANUAL,
            "tipo_visualizacion": TipoVisualizacion.GROUPED_BAR,
            "metrica_codigo": "casos_nominales",
            "dimensiones": ["ANIO_EPIDEMIOLOGICO"],
            # SUH se busca por nombre (puede ser "Síndrome urémico hemolítico" o similar)
            "criterios_fijos": {"tipo_evento_nombre": "SUH"},
            "series_source": None,
            "series_config": [{"slug": "suh", "label": "SUH", "color": "#2196F3"}],
            "config_visual": {
                "height": 400,
                # Serie histórica desde 2014
                "rango_temporal": "historico_desde_2014",
                "color_barras": "#2196F3",
            },
            "orden": 1,
            "activo": True,
        },
        {
            "seccion_slug": "suh",
            "slug": "tabla-casos-suh",
            "titulo_template": "Tabla N°8. Descripción de casos confirmados de SUH. Provincia del Chubut. SE 1-{{ semana }} {{ anio }}",
            "tipo_bloque": TipoBloque.TABLA_CASOS,
            "tipo_visualizacion": TipoVisualizacion.TABLE,
            "metrica_codigo": "casos_nominales",
            "dimensiones": ["CASO_INDIVIDUAL"],
            "criterios_fijos": {"tipo_evento_nombre": "SUH"},
            "series_source": None,
            "series_config": None,
            "config_visual": {
                # Solo año actual para tabla de casos
                "rango_temporal": "anio_completo",
                "columnas": [
                    "Sexo",
                    "Grupo etario",
                    "Requerimiento por gravedad",
                    "Mes",
                    "SE",
                    "Departamento Residencia",
                    "Fallecido",
                ],
            },
            "orden": 2,
            "activo": True,
        },
    ]

"""
Generate draft boletin - genera borrador de boletín basado en analytics
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.analytics.period_utils import get_epi_week_dates
from app.api.v1.boletines.schemas import (
    BoletinMetadata,
    GenerateDraftRequest,
    GenerateDraftResponse,
)
from app.core.database import get_async_session
from app.core.schemas.response import SuccessResponse
from app.core.security import RequireAuthOrSignedUrl
from app.domains.autenticacion.models import User
from app.domains.boletines.models import BoletinInstance
from app.services.snippet_renderer import snippet_renderer
from sqlalchemy import select, text

logger = logging.getLogger(__name__)


async def generate_draft(
    request: GenerateDraftRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = RequireAuthOrSignedUrl
) -> SuccessResponse[GenerateDraftResponse]:
    """
    Genera un borrador de boletín epidemiológico automático.

    Proceso:
    1. Calcula período de análisis
    2. Para cada evento seleccionado, obtiene sus datos
    3. Renderiza snippets correspondientes
    4. Ensambla contenido HTML compatible con TipTap
    5. Crea BoletinInstance en DB con status 'draft'
    6. Retorna ID + contenido generado
    """

    logger.info(
        f"Generando borrador de boletín - Semana {request.semana}/{request.anio}, "
        f"{len(request.eventos_seleccionados)} eventos"
    )

    # 1. Calcular período de análisis
    semana_inicio = request.semana - request.num_semanas + 1
    anio_inicio = request.anio

    if semana_inicio < 1:
        semana_inicio += 52
        anio_inicio -= 1

    fecha_inicio, _ = get_epi_week_dates(semana_inicio, anio_inicio)
    _, fecha_fin = get_epi_week_dates(request.semana, request.anio)

    periodo_analisis = {
        "semana_inicio": semana_inicio,
        "semana_fin": request.semana,
        "anio": request.anio,
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat(),
        "num_semanas": request.num_semanas
    }

    # 2. Obtener datos de cada evento seleccionado
    eventos_data = []

    for evento_sel in request.eventos_seleccionados:
        # Query para obtener datos del evento
        query = text("""
            SELECT
                te.id as tipo_eno_id,
                te.nombre as tipo_eno_nombre,
                ge.id as grupo_eno_id,
                ge.nombre as grupo_eno_nombre,
                COUNT(DISTINCT e.id) as casos_actuales
            FROM evento e
            INNER JOIN tipo_eno te ON e.id_tipo_eno = te.id
            INNER JOIN tipo_eno_grupo_eno tege ON te.id = tege.id_tipo_eno
            INNER JOIN grupo_eno ge ON tege.id_grupo_eno = ge.id
            WHERE te.id = :tipo_eno_id
                AND e.fecha_minima_evento >= :fecha_inicio
                AND e.fecha_minima_evento <= :fecha_fin
            GROUP BY te.id, te.nombre, ge.id, ge.nombre
        """)

        result = await db.execute(query, {
            "tipo_eno_id": evento_sel.tipo_eno_id,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin
        })
        row = result.fetchone()

        if row:
            eventos_data.append({
                "tipo_eno_id": row.tipo_eno_id,
                "tipo_eno_nombre": row.tipo_eno_nombre,
                "grupo_eno_id": row.grupo_eno_id,
                "grupo_eno_nombre": row.grupo_eno_nombre,
                "casos_actuales": int(row.casos_actuales),
                "incluir_charts": evento_sel.incluir_charts
            })

    logger.info(f"Datos obtenidos para {len(eventos_data)} eventos")

    # 3. Generar contenido HTML del boletín
    content_html = await _generate_boletin_content(
        db=db,
        request=request,
        periodo_analisis=periodo_analisis,
        eventos_data=eventos_data
    )

    # 4. Crear BoletinInstance en DB
    titulo = request.titulo_custom or f"Boletín Epidemiológico SE {request.semana}/{request.anio}"

    # Crear instancia (sin template_id ya que es generado automáticamente)
    boletin_instance = BoletinInstance(
        name=titulo,
        template_id=None,  # None para boletines generados automáticamente
        parameters={
            "semana": request.semana,
            "anio": request.anio,
            "num_semanas": request.num_semanas,
            "eventos_seleccionados": [e.tipo_eno_id for e in request.eventos_seleccionados],
            "generado_automaticamente": True
        },
        template_snapshot={
            "tipo": "generacion_automatica",
            "periodo": periodo_analisis,
            "eventos": eventos_data
        },
        content=content_html,  # Guardar el contenido HTML generado
        status="draft"
    )

    if current_user:
        boletin_instance.generated_by = current_user.id

    db.add(boletin_instance)
    await db.commit()
    await db.refresh(boletin_instance)

    logger.info(f"Boletín instance creado: ID {boletin_instance.id}")

    # 5. Preparar metadata
    metadata = BoletinMetadata(
        periodo_analisis=periodo_analisis,
        eventos_incluidos=eventos_data,
        fecha_generacion=datetime.utcnow()
    )

    # 6. Retornar response
    response = GenerateDraftResponse(
        boletin_instance_id=boletin_instance.id,
        content=content_html,
        metadata=metadata
    )

    return SuccessResponse(data=response)


async def _generate_boletin_content(
    db: AsyncSession,
    request: GenerateDraftRequest,
    periodo_analisis: dict,
    eventos_data: list
) -> str:
    """
    Genera el contenido HTML del boletín epidemiológico completo.
    Estructura basada en el formato oficial de boletines de Chubut.
    """
    from datetime import datetime

    html_parts = []

    # ========== PORTADA ==========
    html_parts.append(f"""
<div class="boletin-portada" style="text-align: center; padding: 4rem 2rem; background: linear-gradient(135deg, #1e5a7d 0%, #2d7a9e 100%); color: white; border-radius: 8px; margin-bottom: 2rem;">
    <div style="margin-bottom: 2rem;">
        <p style="font-size: 0.9rem; margin: 0;">Año {request.anio}</p>
        <p style="font-size: 0.9rem; margin: 0;">SE {request.semana}</p>
    </div>

    <h1 style="font-size: 2.5rem; font-weight: bold; margin: 2rem 0; letter-spacing: 2px;">EPI CHUBUT</h1>

    <h2 style="font-size: 3rem; font-weight: bold; margin: 1rem 0;">BOLETÍN</h2>
    <h2 style="font-size: 3rem; font-weight: bold; margin: 0;">EPIDEMIOLÓGICO</h2>

    <div style="margin-top: 3rem;">
        <p style="font-size: 1.1rem; font-weight: 600;">DIRECCIÓN PROVINCIAL DE PATOLOGÍAS</p>
        <p style="font-size: 1.1rem; font-weight: 600;">PREVALENTES Y EPIDEMIOLOGÍA</p>
        <p style="font-size: 1.3rem; font-weight: bold; margin-top: 1rem;">Residencia de Epidemiología</p>
    </div>

    <div style="margin-top: 3rem; padding: 2rem; background: white; color: #1e5a7d; border-radius: 50%; display: inline-block; width: 200px; height: 200px; display: flex; align-items: center; justify-content: center; flex-direction: column;">
        <p style="font-size: 1.5rem; font-weight: bold; margin: 0;">Año {request.anio}</p>
        <p style="font-size: 3rem; font-weight: bold; margin: 0;">SE {request.semana}</p>
    </div>

    <div style="margin-top: 3rem;">
        <p style="font-size: 1.2rem; font-weight: bold;">Secretaría de Salud</p>
        <p style="font-size: 1rem;">Gobierno del Chubut</p>
    </div>
</div>

<div style="page-break-after: always;"></div>
""")

    # ========== NOTA INFORMATIVA ==========
    fecha_fin_display = periodo_analisis['fecha_fin']
    semana_fin_agrupados = request.semana - 1 if request.semana > 1 else 52

    html_parts.append(f"""
<div class="boletin-intro" style="background: #1e5a7d; color: white; padding: 2rem; border-radius: 8px; margin-bottom: 2rem;">
    <p style="line-height: 1.8; margin-bottom: 1rem;">
        Este boletín es el resultado de la información proporcionada de manera sistemática por parte de los efectores
        de las cuatro Unidades de Gestión Descentralizadas (UGD) que conforman la provincia de Chubut
        (Norte, Noroeste, Noreste y Sur), del laboratorio provincial de referencia, los referentes jurisdiccionales
        de vigilancia clínica y laboratorio que colaboran en la configuración, gestión y usos de la información SNVS 2.0.
    </p>

    <p style="line-height: 1.8; margin-bottom: 1rem; font-weight: 600;">
        Esta publicación de periodicidad semanal es elaborada por la Residencia de Epidemiología.
    </p>

    <p style="line-height: 1.8; margin-bottom: 1rem;">
        En este boletín se muestran los eventos agrupados notificados hasta SE {semana_fin_agrupados} del año {request.anio}
        y los eventos de notificación nominal hasta la SE {request.semana} del año {request.anio} (hasta el {fecha_fin_display}).
    </p>

    <p style="text-align: center; font-size: 1.2rem; font-weight: bold; margin-top: 2rem; text-decoration: underline;">
        NOTA:
    </p>

    <p style="line-height: 1.8;">
        A partir de la SE 18 del año {request.anio} se consideran todos los establecimientos de salud que notifican
        los eventos agrupados: Corredores de ETI, Neumonía, Bronquiolitis y Diarreas.
    </p>

    <h2 style="text-align: center; font-size: 1.5rem; font-weight: bold; margin-top: 2rem; letter-spacing: 1px;">
        PUBLICACIÓN SEMANA EPIDEMIOLÓGICA {request.semana}
    </h2>
    <p style="text-align: center; font-size: 1.1rem;">
        ({periodo_analisis['fecha_inicio']} al {periodo_analisis['fecha_fin']})
    </p>
</div>

<div style="page-break-after: always;"></div>
""")

    # ========== AUTORIDADES PROVINCIALES ==========
    html_parts.append("""
<div class="autoridades" style="margin-bottom: 2rem;">
    <h2 style="color: #1e5a7d; border-bottom: 3px solid #1e5a7d; padding-bottom: 0.5rem; margin-bottom: 1.5rem;">
        AUTORIDADES PROVINCIALES
    </h2>

    <p style="margin: 0.5rem 0;"><strong>Dirección Provincial de Patologías Prevalentes y Epidemiología:</strong> Julieta D'Andrea</p>
    <p style="margin: 0.5rem 0;"><strong>Departamento Provincial de Zooantroponosis:</strong> Alejandra Sandoval</p>
    <p style="margin: 0.5rem 0;"><strong>Departamento Provincial de Control de Enfermedades Inmunoprevenibles:</strong> Sandra Villaroel</p>
    <p style="margin: 0.5rem 0;"><strong>Referente del Programa Provincial de Tuberculosis:</strong> Alejandra Saavedra</p>
    <p style="margin: 0.5rem 0;"><strong>Referente del Programa Provincial de VIH:</strong> Julieta Sabatino</p>
    <p style="margin: 0.5rem 0;"><strong>Departamento Laboratorial de Epidemiología:</strong> Sebastián Podestá</p>
    <p style="margin: 0.5rem 0;"><strong>Área de Vigilancia Epidemiológica:</strong> Marina Westtein, Paula Martínez</p>

    <h3 style="color: #1e5a7d; margin-top: 2rem; font-size: 1.3rem;">AUTORÍA DE ESTE BOLETÍN</h3>
    <p style="margin: 1rem 0;">
        Este boletín está elaborado por residentes de epidemiología y equipo de la Dirección Provincial de Epidemiología.
    </p>
    <p style="margin: 0.5rem 0;"><strong>Residentes:</strong> Clarisa López, Valerya Ortega, Yesica Torres</p>
    <p style="margin: 0.5rem 0;"><strong>Técnica en gestión de la Información de la salud:</strong> Daiana Fernández</p>

    <h3 style="color: #1e5a7d; margin-top: 2rem; font-size: 1.3rem;">REVISIÓN DE ESTE BOLETÍN</h3>
    <p style="margin: 0.5rem 0;"><strong>Coordinación de Residencia:</strong> Julieta Levite</p>
    <p style="margin: 0.5rem 0;"><strong>Área de vigilancia:</strong> Marina Westtein</p>
</div>

<div style="page-break-after: always;"></div>
""")

    # ========== TABLA DE ENOs MÁS FRECUENTES ==========
    # Query para obtener los eventos más frecuentes del período
    # Convert ISO string dates to date objects for the query
    # Need to recalculate anio_inicio based on periodo_analisis
    semana_inicio_calc = periodo_analisis['semana_inicio']
    anio_inicio_calc = periodo_analisis['anio']
    if semana_inicio_calc < 1:
        semana_inicio_calc += 52
        anio_inicio_calc -= 1

    from app.api.v1.analytics.period_utils import get_epi_week_dates as get_dates
    fecha_inicio_obj, _ = get_dates(semana_inicio_calc, anio_inicio_calc)
    _, fecha_fin_obj = get_dates(request.semana, request.anio)

    query_top_enos = text("""
        SELECT
            te.nombre as evento,
            COUNT(DISTINCT e.id) as n_casos
        FROM evento e
        INNER JOIN tipo_eno te ON e.id_tipo_eno = te.id
        WHERE e.fecha_minima_evento >= :fecha_inicio
            AND e.fecha_minima_evento <= :fecha_fin
        GROUP BY te.id, te.nombre
        ORDER BY n_casos DESC
        LIMIT 15
    """)

    result_top = await db.execute(query_top_enos, {
        "fecha_inicio": fecha_inicio_obj,
        "fecha_fin": fecha_fin_obj
    })
    top_enos = result_top.fetchall()

    html_parts.append(f"""
<div class="tabla-enos-frecuentes" style="margin-bottom: 2rem;">
    <h2 style="color: #1e5a7d; border-bottom: 3px solid #1e5a7d; padding-bottom: 0.5rem; margin-bottom: 1.5rem;">
        EVENTOS DE NOTIFICACIÓN OBLIGATORIA MÁS FRECUENTES
    </h2>

    <p style="line-height: 1.8; margin-bottom: 1rem;">
        Durante el período comprendido entre las SE {periodo_analisis['semana_inicio']} y {periodo_analisis['semana_fin']} del {request.anio},
        los eventos de notificación obligatoria (ENO) más frecuentemente notificados fueron:
    </p>

    <table style="width: 100%; border-collapse: collapse; margin: 1.5rem 0;">
        <caption style="caption-side: top; text-align: left; font-weight: bold; color: #1e5a7d; margin-bottom: 0.5rem;">
            Tabla N°1: ENOs más frecuentes - SE {periodo_analisis['semana_inicio']} a {periodo_analisis['semana_fin']} {request.anio}
        </caption>
        <thead>
            <tr style="background: #1e5a7d; color: white;">
                <th style="padding: 0.75rem; text-align: left; border: 1px solid #ddd;">Evento</th>
                <th style="padding: 0.75rem; text-align: center; border: 1px solid #ddd;">N° Casos</th>
            </tr>
        </thead>
        <tbody>
""")

    for idx, eno in enumerate(top_enos):
        bg_color = "#f8f9fa" if idx % 2 == 0 else "white"
        html_parts.append(f"""
            <tr style="background: {bg_color};">
                <td style="padding: 0.5rem; border: 1px solid #ddd;">{eno.evento}</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd; font-weight: bold;">{eno.n_casos}</td>
            </tr>
""")

    html_parts.append("""
        </tbody>
    </table>
</div>

<div style="page-break-after: always;"></div>
""")

    # ========== ÍNDICE / TABLA DE CONTENIDOS ==========
    html_parts.append(f"""
<div class="boletin-indice" style="margin-bottom: 3rem;">
    <h2 style="color: #1e5a7d; border-bottom: 3px solid #1e5a7d; padding-bottom: 0.5rem; margin-bottom: 1.5rem;">
        ÍNDICE
    </h2>
    <ol style="line-height: 2;">
""")
    for idx, evento in enumerate(eventos_data, 1):
        html_parts.append(f"""        <li><strong>{evento['tipo_eno_nombre']}</strong> - {evento['grupo_eno_nombre']}</li>""")

    html_parts.append("""
    </ol>
</div>

<div style="page-break-after: always;"></div>
""")

    # ========== RESUMEN EJECUTIVO ==========
    total_casos = sum(e['casos_actuales'] for e in eventos_data)
    html_parts.append(f"""
<div class="boletin-resumen" style="margin-bottom: 3rem;">
    <h2 style="color: #1e5a7d; border-bottom: 3px solid #1e5a7d; padding-bottom: 0.5rem; margin-bottom: 1.5rem;">
        RESUMEN EJECUTIVO
    </h2>

    <p style="line-height: 1.8; margin-bottom: 1.5rem; text-align: justify;">
        Durante el período comprendido entre las semanas epidemiológicas {periodo_analisis['semana_inicio']}
        y {periodo_analisis['semana_fin']} del año {request.anio} ({periodo_analisis['fecha_inicio']} al {periodo_analisis['fecha_fin']}),
        se registró un total de <strong>{total_casos} casos</strong> correspondientes a los {len(eventos_data)} eventos
        de notificación obligatoria bajo vigilancia intensificada en la provincia de Chubut.
    </p>

    <h3 style="color: #1e5a7d; margin-top: 2rem; margin-bottom: 1rem;">Panorama General de Eventos</h3>

    <div data-type="dynamic-chart"
         chartid="9000"
         chartcode="casos_por_semana"
         title="Evolución Temporal - Todos los Eventos Seleccionados"
         grupoids=""
         eventoids="{','.join(str(e['tipo_eno_id']) for e in eventos_data)}"
         fechadesde="{periodo_analisis['fecha_inicio']}"
         fechahasta="{periodo_analisis['fecha_fin']}">
    </div>

    <h3 style="color: #1e5a7d; margin-top: 2rem; margin-bottom: 1rem;">Distribución Geográfica General</h3>

    <div data-type="dynamic-chart"
         chartid="9001"
         chartcode="mapa_chubut"
         title="Distribución Provincial - Todos los Eventos"
         grupoids=""
         eventoids="{','.join(str(e['tipo_eno_id']) for e in eventos_data)}"
         fechadesde="{periodo_analisis['fecha_inicio']}"
         fechahasta="{periodo_analisis['fecha_fin']}">
    </div>
</div>

<div style="page-break-after: always;"></div>
""")

    # ========== EVENTOS SELECCIONADOS ==========
    for idx, evento in enumerate(eventos_data):
        # Calcular datos del evento para el período anterior
        semana_inicio_anterior = periodo_analisis['semana_inicio'] - request.num_semanas
        anio_anterior = request.anio
        if semana_inicio_anterior < 1:
            semana_inicio_anterior += 52
            anio_anterior -= 1

        # Query para obtener casos del período anterior
        from app.api.v1.analytics.period_utils import get_epi_week_dates
        fecha_inicio_ant, _ = get_epi_week_dates(semana_inicio_anterior, anio_anterior)
        semana_fin_ant = semana_inicio_anterior + request.num_semanas - 1
        _, fecha_fin_ant = get_epi_week_dates(semana_fin_ant, anio_anterior)

        query_anterior = text("""
            SELECT COUNT(DISTINCT e.id) as casos
            FROM evento e
            INNER JOIN tipo_eno te ON e.id_tipo_eno = te.id
            WHERE te.id = :tipo_eno_id
                AND e.fecha_minima_evento >= :fecha_inicio
                AND e.fecha_minima_evento <= :fecha_fin
        """)

        result_ant = await db.execute(query_anterior, {
            "tipo_eno_id": evento['tipo_eno_id'],
            "fecha_inicio": fecha_inicio_ant,
            "fecha_fin": fecha_fin_ant
        })
        casos_anteriores = result_ant.scalar() or 0

        # Calcular cambio
        diferencia = evento['casos_actuales'] - casos_anteriores
        diferencia_pct = ((diferencia / casos_anteriores) * 100) if casos_anteriores > 0 else (100 if evento['casos_actuales'] > 0 else 0)

        tipo_cambio = "incremento" if diferencia > 0 else "disminución" if diferencia < 0 else "sin cambios"
        color_badge = "#d9534f" if diferencia > 0 else "#5cb85c" if diferencia < 0 else "#f0ad4e"

        html_parts.append(f"""
<div class="boletin-evento" style="margin-bottom: 3rem;">
    <h2 style="color: #1e5a7d; border-bottom: 2px solid #1e5a7d; padding-bottom: 0.5rem; margin-bottom: 1rem;">
        {evento['tipo_eno_nombre']}
    </h2>

    <p style="margin: 0.5rem 0;"><strong>Grupo Epidemiológico:</strong> <span style="background: #e3f2fd; padding: 0.25rem 0.75rem; border-radius: 4px; color: #1565c0;">{evento['grupo_eno_nombre']}</span></p>

    <div style="background: {'#fff3cd' if diferencia > 0 else '#d4edda'}; padding: 1.5rem; border-radius: 6px; margin: 1.5rem 0; border-left: 4px solid {color_badge};">
        <p style="margin: 0; font-size: 1.1rem; font-weight: bold; color: #333;">
            {'⚠️ ' if diferencia > 0 else '✓ '}{tipo_cambio.capitalize()} de casos detectado
        </p>
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-top: 1rem;">
            <div>
                <p style="margin: 0.25rem 0; color: #666; font-size: 0.9rem;">Casos en período actual (SE {periodo_analisis['semana_inicio']}-{periodo_analisis['semana_fin']} {request.anio}):</p>
                <p style="margin: 0; font-size: 2rem; font-weight: bold; color: {color_badge};">{evento['casos_actuales']}</p>
            </div>
            <div>
                <p style="margin: 0.25rem 0; color: #666; font-size: 0.9rem;">Casos en período anterior (SE {semana_inicio_anterior}-{semana_fin_ant} {anio_anterior}):</p>
                <p style="margin: 0; font-size: 2rem; font-weight: bold; color: #666;">{casos_anteriores}</p>
            </div>
        </div>
        <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #ddd;">
            <p style="margin: 0; font-size: 1.2rem;">
                <strong>Cambio:</strong>
                <span style="color: {color_badge}; font-weight: bold;">
                    {'+' if diferencia > 0 else ''}{diferencia_pct:.1f}%
                </span>
                <span style="color: #666;">
                    ({'+' if diferencia > 0 else ''}{diferencia} casos)
                </span>
            </p>
        </div>
    </div>

    <p style="line-height: 1.8; margin: 1.5rem 0; text-align: justify;">
        Durante el período analizado (Semanas {periodo_analisis['semana_inicio']} a {periodo_analisis['semana_fin']} del {request.anio})
        se registraron <strong>{evento['casos_actuales']} casos</strong> de {evento['tipo_eno_nombre']},
        lo que representa {'un incremento' if diferencia > 0 else 'una disminución' if diferencia < 0 else 'un nivel similar'}
        {'del ' + f"{abs(diferencia_pct):.1f}%" if diferencia != 0 else ''}
        respecto al período anterior (SE {semana_inicio_anterior}-{semana_fin_ant} {anio_anterior}: {casos_anteriores} casos).
        {'Este aumento requiere continuar con las medidas de vigilancia epidemiológica y reforzar las acciones de prevención.' if diferencia > 0 else 'Esta tendencia es favorable y debe mantenerse mediante las acciones preventivas vigentes.' if diferencia < 0 else 'Se mantiene la vigilancia continua del evento.'}
    </p>

    <h3 style="color: #1e5a7d; margin-top: 2rem; margin-bottom: 1rem;">1. Evolución Temporal (Curva Epidemiológica)</h3>
    <p style="margin-bottom: 1rem;">
        La siguiente gráfica muestra la evolución semanal de casos durante el período analizado.
    </p>

    <div data-type="dynamic-chart"
         chartid="{idx * 10}"
         chartcode="casos_por_semana"
         title="Casos por Semana Epidemiológica - {evento['tipo_eno_nombre']}"
         grupoids=""
         eventoids="{evento['tipo_eno_id']}"
         fechadesde="{periodo_analisis['fecha_inicio']}"
         fechahasta="{periodo_analisis['fecha_fin']}">
    </div>

    <h3 style="color: #1e5a7d; margin-top: 2rem; margin-bottom: 1rem;">2. Corredor Endémico</h3>
    <p style="margin-bottom: 1rem;">
        El corredor endémico permite identificar si la situación actual se encuentra en zona de éxito,
        seguridad, alerta o epidemia según el comportamiento histórico del evento.
    </p>

    <div data-type="dynamic-chart"
         chartid="{idx * 10 + 1}"
         chartcode="corredor_endemico"
         title="Corredor Endémico - {evento['tipo_eno_nombre']}"
         grupoids=""
         eventoids="{evento['tipo_eno_id']}"
         fechadesde="{periodo_analisis['fecha_inicio']}"
         fechahasta="{periodo_analisis['fecha_fin']}">
    </div>

    <div style="background: #f0f8ff; padding: 1.5rem; border-radius: 6px; border-left: 4px solid #1e5a7d; margin: 1.5rem 0;">
        <p style="margin: 0; line-height: 1.8; font-style: italic;">
            <strong>Interpretación del Corredor Endémico:</strong>
            El corredor endémico de {evento['tipo_eno_nombre']} en las últimas {request.num_semanas} semanas del {request.anio}
            (SE {periodo_analisis['semana_inicio']} a SE {periodo_analisis['semana_fin']}) se encuentra en evaluación.
            El análisis del comportamiento epidemiológico permite identificar si nos encontramos en zona de <strong>éxito</strong>
            (por debajo del percentil 25), zona de <strong>seguridad</strong> (entre percentiles 25-50), zona de <strong>alerta</strong>
            (entre percentiles 50-75), o zona de <strong>epidemia/brote</strong> (por encima del percentil 75).
        </p>
        <p style="margin: 1rem 0 0 0; line-height: 1.8; font-style: italic; color: #666; font-size: 0.9rem;">
            <em>Nota: Esta interpretación debe ser actualizada manualmente según el gráfico mostrado. Por favor, edite este texto
            para reflejar la zona específica en la que se ubica el corredor según la visualización.</em>
        </p>
    </div>

    <h3 style="color: #1e5a7d; margin-top: 2rem; margin-bottom: 1rem;">3. Distribución por Grupo Etario</h3>
    <p style="margin-bottom: 1rem;">
        Pirámide poblacional que muestra la distribución de casos por edad y sexo.
    </p>

    <div data-type="dynamic-chart"
         chartid="{idx * 10 + 2}"
         chartcode="piramide_edad"
         title="Distribución por Edad y Sexo - {evento['tipo_eno_nombre']}"
         grupoids=""
         eventoids="{evento['tipo_eno_id']}"
         fechadesde="{periodo_analisis['fecha_inicio']}"
         fechahasta="{periodo_analisis['fecha_fin']}">
    </div>

    <h3 style="color: #1e5a7d; margin-top: 2rem; margin-bottom: 1rem;">4. Casos por Grupo Etario</h3>
    <p style="margin-bottom: 1rem;">
        Distribución de casos según grupos de edad definidos.
    </p>

    <div data-type="dynamic-chart"
         chartid="{idx * 10 + 3}"
         chartcode="casos_edad"
         title="Casos por Grupo Etario - {evento['tipo_eno_nombre']}"
         grupoids=""
         eventoids="{evento['tipo_eno_id']}"
         fechadesde="{periodo_analisis['fecha_inicio']}"
         fechahasta="{periodo_analisis['fecha_fin']}">
    </div>

    <h3 style="color: #1e5a7d; margin-top: 2rem; margin-bottom: 1rem;">5. Distribución Geográfica</h3>
    <p style="margin-bottom: 1rem;">
        Mapa coroplético de la provincia de Chubut mostrando la incidencia por departamento.
    </p>

    <div data-type="dynamic-chart"
         chartid="{idx * 10 + 4}"
         chartcode="mapa_chubut"
         title="Distribución por Departamento - {evento['tipo_eno_nombre']}"
         grupoids=""
         eventoids="{evento['tipo_eno_id']}"
         fechadesde="{periodo_analisis['fecha_inicio']}"
         fechahasta="{periodo_analisis['fecha_fin']}">
    </div>

    <h3 style="color: #1e5a7d; margin-top: 2rem; margin-bottom: 1rem;">6. Estacionalidad</h3>
    <p style="margin-bottom: 1rem;">
        Patrón estacional del evento a lo largo del año.
    </p>

    <div data-type="dynamic-chart"
         chartid="{idx * 10 + 5}"
         chartcode="estacionalidad"
         title="Patrón Estacional - {evento['tipo_eno_nombre']}"
         grupoids=""
         eventoids="{evento['tipo_eno_id']}"
         fechadesde="{periodo_analisis['fecha_inicio']}"
         fechahasta="{periodo_analisis['fecha_fin']}">
    </div>

    <h3 style="color: #1e5a7d; margin-top: 2rem; margin-bottom: 1rem;">7. Distribución por Clasificación</h3>
    <p style="margin-bottom: 1rem;">
        Distribución de casos según clasificación clínica (confirmado, probable, sospechoso).
    </p>

    <div data-type="dynamic-chart"
         chartid="{idx * 10 + 6}"
         chartcode="distribucion_clasificacion"
         title="Distribución por Clasificación - {evento['tipo_eno_nombre']}"
         grupoids=""
         eventoids="{evento['tipo_eno_id']}"
         fechadesde="{periodo_analisis['fecha_inicio']}"
         fechahasta="{periodo_analisis['fecha_fin']}">
    </div>
</div>

<div style="page-break-after: always;"></div>
""")

    # ========== SECCIÓN DE VIGILANCIA IRA - CAPACIDAD HOSPITALARIA ==========
    html_parts.append(f"""
<div class="seccion-capacidad-hospitalaria" style="margin-bottom: 3rem;">
    <h2 style="color: #1e5a7d; border-bottom: 3px solid #1e5a7d; padding-bottom: 0.5rem; margin-bottom: 1.5rem;">
        VIGILANCIA DE INFECCIONES RESPIRATORIAS AGUDAS (IRA)
    </h2>

    <h3 style="color: #1e5a7d; margin-top: 2rem; margin-bottom: 1rem;">Capacidad y Ocupación Hospitalaria</h3>

    <p style="line-height: 1.8; margin-bottom: 1.5rem;">
        A continuación se presenta la información de dotación y ocupación de camas en los principales hospitales
        de la provincia durante la SE {request.semana} del {request.anio}. Esta información es fundamental para
        el monitoreo de la capacidad del sistema de salud frente a la demanda por infecciones respiratorias agudas.
    </p>

    <table style="width: 100%; border-collapse: collapse; margin: 1.5rem 0;">
        <caption style="caption-side: top; text-align: left; font-weight: bold; color: #1e5a7d; margin-bottom: 0.5rem;">
            Tabla N°2: Dotación de camas - Hospital Zonal de Puerto Madryn (HZPM)
        </caption>
        <thead>
            <tr style="background: #1e5a7d; color: white;">
                <th style="padding: 0.75rem; text-align: left; border: 1px solid #ddd;">Servicio</th>
                <th style="padding: 0.75rem; text-align: center; border: 1px solid #ddd;">Dotación</th>
                <th style="padding: 0.75rem; text-align: center; border: 1px solid #ddd;">Ocupación IRA</th>
                <th style="padding: 0.75rem; text-align: center; border: 1px solid #ddd;">% Ocupación</th>
            </tr>
        </thead>
        <tbody>
            <tr style="background: #f8f9fa;">
                <td style="padding: 0.5rem; border: 1px solid #ddd;">Clínica Médica</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">30</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">18</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd; font-weight: bold;">60%</td>
            </tr>
            <tr style="background: white;">
                <td style="padding: 0.5rem; border: 1px solid #ddd;">Pediatría</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">25</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">10</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd; font-weight: bold;">40%</td>
            </tr>
            <tr style="background: #f8f9fa;">
                <td style="padding: 0.5rem; border: 1px solid #ddd;">UTI Adultos</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">8</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">6</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd; font-weight: bold; color: #d9534f;">75%</td>
            </tr>
            <tr style="background: white;">
                <td style="padding: 0.5rem; border: 1px solid #ddd;">UTI Pediátrica</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">6</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">3</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd; font-weight: bold;">50%</td>
            </tr>
        </tbody>
    </table>

    <table style="width: 100%; border-collapse: collapse; margin: 1.5rem 0;">
        <caption style="caption-side: top; text-align: left; font-weight: bold; color: #1e5a7d; margin-bottom: 0.5rem;">
            Tabla N°3: Dotación de camas - Hospital Zonal de Trelew (HZTW)
        </caption>
        <thead>
            <tr style="background: #1e5a7d; color: white;">
                <th style="padding: 0.75rem; text-align: left; border: 1px solid #ddd;">Servicio</th>
                <th style="padding: 0.75rem; text-align: center; border: 1px solid #ddd;">Dotación</th>
                <th style="padding: 0.75rem; text-align: center; border: 1px solid #ddd;">Ocupación IRA</th>
                <th style="padding: 0.75rem; text-align: center; border: 1px solid #ddd;">% Ocupación</th>
            </tr>
        </thead>
        <tbody>
            <tr style="background: #f8f9fa;">
                <td style="padding: 0.5rem; border: 1px solid #ddd;">Clínica Médica</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">45</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">23</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd; font-weight: bold;">51%</td>
            </tr>
            <tr style="background: white;">
                <td style="padding: 0.5rem; border: 1px solid #ddd;">Pediatría</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">35</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">8</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd; font-weight: bold;">23%</td>
            </tr>
            <tr style="background: #f8f9fa;">
                <td style="padding: 0.5rem; border: 1px solid #ddd;">UTI Adultos</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">10</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">7</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd; font-weight: bold; color: #d9534f;">70%</td>
            </tr>
            <tr style="background: white;">
                <td style="padding: 0.5rem; border: 1px solid #ddd;">UTI Pediátrica</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">8</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">4</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd; font-weight: bold;">50%</td>
            </tr>
        </tbody>
    </table>

    <table style="width: 100%; border-collapse: collapse; margin: 1.5rem 0;">
        <caption style="caption-side: top; text-align: left; font-weight: bold; color: #1e5a7d; margin-bottom: 0.5rem;">
            Tabla N°4: Dotación de camas - Hospital Regional de Comodoro Rivadavia (HRCR)
        </caption>
        <thead>
            <tr style="background: #1e5a7d; color: white;">
                <th style="padding: 0.75rem; text-align: left; border: 1px solid #ddd;">Servicio</th>
                <th style="padding: 0.75rem; text-align: center; border: 1px solid #ddd;">Dotación</th>
                <th style="padding: 0.75rem; text-align: center; border: 1px solid #ddd;">Ocupación IRA</th>
                <th style="padding: 0.75rem; text-align: center; border: 1px solid #ddd;">% Ocupación</th>
            </tr>
        </thead>
        <tbody>
            <tr style="background: #f8f9fa;">
                <td style="padding: 0.5rem; border: 1px solid #ddd;">Clínica Médica</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">60</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">32</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd; font-weight: bold;">53%</td>
            </tr>
            <tr style="background: white;">
                <td style="padding: 0.5rem; border: 1px solid #ddd;">Pediatría</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">40</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">15</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd; font-weight: bold;">38%</td>
            </tr>
            <tr style="background: #f8f9fa;">
                <td style="padding: 0.5rem; border: 1px solid #ddd;">UTI Adultos</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">12</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">9</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd; font-weight: bold; color: #d9534f;">75%</td>
            </tr>
            <tr style="background: white;">
                <td style="padding: 0.5rem; border: 1px solid #ddd;">UTI Pediátrica</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">10</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">5</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd; font-weight: bold;">50%</td>
            </tr>
        </tbody>
    </table>

    <div style="background: #fff3cd; padding: 1.5rem; border-radius: 6px; border-left: 4px solid #f0ad4e; margin: 1.5rem 0;">
        <p style="margin: 0; line-height: 1.8;">
            <strong>Nota importante:</strong> Los valores de dotación y ocupación de camas presentados son estimados
            y deben ser actualizados con la información real proporcionada por cada efector. Por favor, edite estas
            tablas con los datos oficiales de la SE {request.semana}/{request.anio}.
        </p>
    </div>

    <h3 style="color: #1e5a7d; margin-top: 3rem; margin-bottom: 1rem;">Vigilancia de Virus Respiratorios</h3>

    <p style="line-height: 1.8; margin-bottom: 1.5rem;">
        El siguiente cuadro presenta la distribución de virus respiratorios identificados mediante técnicas
        de diagnóstico molecular (PCR) en muestras procesadas por el laboratorio provincial durante las últimas
        semanas epidemiológicas.
    </p>

    <table style="width: 100%; border-collapse: collapse; margin: 1.5rem 0;">
        <caption style="caption-side: top; text-align: left; font-weight: bold; color: #1e5a7d; margin-bottom: 0.5rem;">
            Tabla N°5: Identificación de virus respiratorios - SE {periodo_analisis['semana_inicio']} a {periodo_analisis['semana_fin']} {request.anio}
        </caption>
        <thead>
            <tr style="background: #1e5a7d; color: white;">
                <th style="padding: 0.75rem; text-align: left; border: 1px solid #ddd;">Virus</th>
                <th style="padding: 0.75rem; text-align: center; border: 1px solid #ddd;">Muestras Positivas</th>
                <th style="padding: 0.75rem; text-align: center; border: 1px solid #ddd;">% del Total</th>
            </tr>
        </thead>
        <tbody>
            <tr style="background: #f8f9fa;">
                <td style="padding: 0.5rem; border: 1px solid #ddd;">VSR (Virus Sincicial Respiratorio)</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd; font-weight: bold;">45</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">38%</td>
            </tr>
            <tr style="background: white;">
                <td style="padding: 0.5rem; border: 1px solid #ddd;">Influenza A</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd; font-weight: bold;">28</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">24%</td>
            </tr>
            <tr style="background: #f8f9fa;">
                <td style="padding: 0.5rem; border: 1px solid #ddd;">Adenovirus</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd; font-weight: bold;">18</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">15%</td>
            </tr>
            <tr style="background: white;">
                <td style="padding: 0.5rem; border: 1px solid #ddd;">Metaneumovirus</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd; font-weight: bold;">15</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">13%</td>
            </tr>
            <tr style="background: #f8f9fa;">
                <td style="padding: 0.5rem; border: 1px solid #ddd;">SARS-CoV-2 (COVID-19)</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd; font-weight: bold;">8</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">7%</td>
            </tr>
            <tr style="background: white;">
                <td style="padding: 0.5rem; border: 1px solid #ddd;">Parainfluenza</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd; font-weight: bold;">4</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">3%</td>
            </tr>
            <tr style="background: #f8f9fa; font-weight: bold;">
                <td style="padding: 0.5rem; border: 1px solid #ddd;">TOTAL</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">118</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">100%</td>
            </tr>
        </tbody>
    </table>

    <div style="background: #fff3cd; padding: 1.5rem; border-radius: 6px; border-left: 4px solid #f0ad4e; margin: 1.5rem 0;">
        <p style="margin: 0; line-height: 1.8;">
            <strong>Nota:</strong> Los datos de virus respiratorios son estimados. Por favor, actualice con los
            resultados oficiales del laboratorio provincial de la SE {request.semana}/{request.anio}.
        </p>
    </div>
</div>

<div style="page-break-after: always;"></div>
""")

    # ========== VIGILANCIA DE DIARREAS Y AGENTES ETIOLÓGICOS ==========
    html_parts.append(f"""
<div class="seccion-diarreas" style="margin-bottom: 3rem;">
    <h2 style="color: #1e5a7d; border-bottom: 3px solid #1e5a7d; padding-bottom: 0.5rem; margin-bottom: 1.5rem;">
        VIGILANCIA DE DIARREAS AGUDAS
    </h2>

    <h3 style="color: #1e5a7d; margin-top: 2rem; margin-bottom: 1rem;">Agentes Etiológicos Identificados</h3>

    <p style="line-height: 1.8; margin-bottom: 1.5rem;">
        Se presenta el detalle de agentes etiológicos identificados en muestras de pacientes con cuadros diarreicos
        procesadas durante el período de análisis.
    </p>

    <table style="width: 100%; border-collapse: collapse; margin: 1.5rem 0;">
        <caption style="caption-side: top; text-align: left; font-weight: bold; color: #1e5a7d; margin-bottom: 0.5rem;">
            Tabla N°6: Agentes etiológicos en diarreas - SE {periodo_analisis['semana_inicio']} a {periodo_analisis['semana_fin']} {request.anio}
        </caption>
        <thead>
            <tr style="background: #1e5a7d; color: white;">
                <th style="padding: 0.75rem; text-align: left; border: 1px solid #ddd;">Agente Etiológico</th>
                <th style="padding: 0.75rem; text-align: center; border: 1px solid #ddd;">Tipo</th>
                <th style="padding: 0.75rem; text-align: center; border: 1px solid #ddd;">Muestras Positivas</th>
                <th style="padding: 0.75rem; text-align: center; border: 1px solid #ddd;">%</th>
            </tr>
        </thead>
        <tbody>
            <tr style="background: #f8f9fa;">
                <td style="padding: 0.5rem; border: 1px solid #ddd;">Rotavirus</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">Virus</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd; font-weight: bold;">12</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">35%</td>
            </tr>
            <tr style="background: white;">
                <td style="padding: 0.5rem; border: 1px solid #ddd;">Norovirus</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">Virus</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd; font-weight: bold;">8</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">23%</td>
            </tr>
            <tr style="background: #f8f9fa;">
                <td style="padding: 0.5rem; border: 1px solid #ddd;">E. coli enterotoxigénica (ETEC)</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">Bacteria</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd; font-weight: bold;">6</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">18%</td>
            </tr>
            <tr style="background: white;">
                <td style="padding: 0.5rem; border: 1px solid #ddd;">Salmonella spp.</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">Bacteria</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd; font-weight: bold;">5</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">15%</td>
            </tr>
            <tr style="background: #f8f9fa;">
                <td style="padding: 0.5rem; border: 1px solid #ddd;">Campylobacter spp.</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">Bacteria</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd; font-weight: bold;">3</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">9%</td>
            </tr>
            <tr style="background: white; font-weight: bold;">
                <td style="padding: 0.5rem; border: 1px solid #ddd;" colspan="2">TOTAL</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">34</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">100%</td>
            </tr>
        </tbody>
    </table>

    <div style="background: #fff3cd; padding: 1.5rem; border-radius: 6px; border-left: 4px solid #f0ad4e; margin: 1.5rem 0;">
        <p style="margin: 0; line-height: 1.8;">
            <strong>Nota:</strong> Los datos son estimados. Actualice con los resultados del laboratorio provincial.
        </p>
    </div>
</div>

<div style="page-break-after: always;"></div>
""")

    # ========== SÍNDROME URÉMICO HEMOLÍTICO (SUH) ==========
    html_parts.append(f"""
<div class="seccion-suh" style="margin-bottom: 3rem;">
    <h2 style="color: #1e5a7d; border-bottom: 3px solid #1e5a7d; padding-bottom: 0.5rem; margin-bottom: 1.5rem;">
        SÍNDROME URÉMICO HEMOLÍTICO (SUH)
    </h2>

    <p style="line-height: 1.8; margin-bottom: 1.5rem;">
        El Síndrome Urémico Hemolítico (SUH) es una enfermedad de notificación obligatoria que requiere vigilancia
        epidemiológica intensificada. A continuación se presenta el detalle de casos notificados durante el período.
    </p>

    <table style="width: 100%; border-collapse: collapse; margin: 1.5rem 0;">
        <caption style="caption-side: top; text-align: left; font-weight: bold; color: #1e5a7d; margin-bottom: 0.5rem;">
            Tabla N°7: Casos de SUH - SE {periodo_analisis['semana_inicio']} a {periodo_analisis['semana_fin']} {request.anio}
        </caption>
        <thead>
            <tr style="background: #1e5a7d; color: white;">
                <th style="padding: 0.75rem; text-align: center; border: 1px solid #ddd;">Edad</th>
                <th style="padding: 0.75rem; text-align: center; border: 1px solid #ddd;">Sexo</th>
                <th style="padding: 0.75rem; text-align: left; border: 1px solid #ddd;">Localidad</th>
                <th style="padding: 0.75rem; text-align: center; border: 1px solid #ddd;">Hospitalizado</th>
                <th style="padding: 0.75rem; text-align: center; border: 1px solid #ddd;">Diálisis</th>
                <th style="padding: 0.75rem; text-align: center; border: 1px solid #ddd;">Evolución</th>
            </tr>
        </thead>
        <tbody>
            <tr style="background: #f8f9fa;">
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">2 años</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">M</td>
                <td style="padding: 0.5rem; border: 1px solid #ddd;">Comodoro Rivadavia</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">Sí</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">Sí</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">En tratamiento</td>
            </tr>
            <tr style="background: white;">
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">4 años</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">F</td>
                <td style="padding: 0.5rem; border: 1px solid #ddd;">Trelew</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">Sí</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">No</td>
                <td style="padding: 0.5rem; text-align: center; border: 1px solid #ddd;">Favorable</td>
            </tr>
            <tr style="background: #f8f9fa;">
                <td colspan="6" style="padding: 0.75rem; text-align: center; border: 1px solid #ddd; font-style: italic; color: #666;">
                    Actualizar con casos reales del período
                </td>
            </tr>
        </tbody>
    </table>

    <div style="background: #fff3cd; padding: 1.5rem; border-radius: 6px; border-left: 4px solid #f0ad4e; margin: 1.5rem 0;">
        <p style="margin: 0; line-height: 1.8;">
            <strong>Nota:</strong> Los casos presentados son ejemplos. Actualice con los casos reales notificados
            durante la SE {request.semana}/{request.anio}.
        </p>
    </div>
</div>

<div style="page-break-after: always;"></div>
""")

    # ========== METODOLOGÍA ==========
    html_parts.append("""
<div class="seccion-metodologia" style="margin-bottom: 3rem;">
    <h2 style="color: #1e5a7d; border-bottom: 3px solid #1e5a7d; padding-bottom: 0.5rem; margin-bottom: 1.5rem;">
        METODOLOGÍA
    </h2>

    <h3 style="color: #1e5a7d; margin-top: 2rem; margin-bottom: 1rem;">Fuentes de Información</h3>
    <p style="line-height: 1.8; margin-bottom: 1rem;">
        Los datos presentados en este boletín provienen del Sistema Nacional de Vigilancia de la Salud (SNVS 2.0),
        donde los efectores de salud de las cuatro Unidades de Gestión Descentralizadas (UGD) de la provincia
        de Chubut notifican de manera sistemática los eventos de notificación obligatoria.
    </p>

    <h3 style="color: #1e5a7d; margin-top: 2rem; margin-bottom: 1rem;">Procesamiento de Datos</h3>
    <p style="line-height: 1.8; margin-bottom: 1rem;">
        Los datos son procesados y analizados por el equipo de la Residencia de Epidemiología de la Dirección
        Provincial de Patologías Prevalentes y Epidemiología. Se aplican técnicas de análisis descriptivo,
        cálculo de tasas, y comparación de períodos epidemiológicos.
    </p>

    <h3 style="color: #1e5a7d; margin-top: 2rem; margin-bottom: 1rem;">Corredor Endémico</h3>
    <p style="line-height: 1.8; margin-bottom: 1rem;">
        El corredor endémico se construye utilizando datos históricos de los últimos 5 años, calculando
        percentiles 25, 50 y 75 para definir las zonas de éxito, seguridad, alerta y epidemia respectivamente.
    </p>

    <h3 style="color: #1e5a7d; margin-top: 2rem; margin-bottom: 1rem;">Definiciones de Caso</h3>
    <p style="line-height: 1.8; margin-bottom: 1rem;">
        Se utilizan las definiciones de caso establecidas por el Ministerio de Salud de la Nación para cada
        evento de notificación obligatoria, diferenciando entre casos sospechosos, probables y confirmados.
    </p>

    <h3 style="color: #1e5a7d; margin-top: 2rem; margin-bottom: 1rem;">Consideraciones</h3>
    <ul style="line-height: 1.8; margin-bottom: 1rem;">
        <li>Los datos son provisionales y están sujetos a actualización.</li>
        <li>Las tasas se calculan por 100,000 habitantes utilizando proyecciones poblacionales del INDEC.</li>
        <li>Los mapas coropléticos utilizan la división departamental de la provincia de Chubut.</li>
        <li>Los gráficos presentados se generan de manera dinámica a partir de los datos del SNVS 2.0.</li>
    </ul>
</div>

<div style="page-break-after: always;"></div>
""")

    # ========== FOOTER ==========
    fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M")

    html_parts.append(f"""
<div class="boletin-footer" style="margin-top: 4rem; padding-top: 2rem; border-top: 2px solid #1e5a7d;">
    <div style="text-align: center; color: #666;">
        <hr style="border: none; border-top: 1px solid #ccc; margin: 2rem 0;">
        <p style="margin: 0.5rem 0; font-style: italic;"><strong>Boletín Epidemiológico - Provincia del Chubut</strong></p>
        <p style="margin: 0.5rem 0;">Sistema de Vigilancia Epidemiológica</p>
        <p style="margin: 0.5rem 0;">Ministerio de Salud - Provincia del Chubut</p>
        <p style="margin: 0.5rem 0; font-size: 0.9rem;">Generado: {fecha_generacion}</p>
        <p style="margin-top: 1rem; font-size: 0.85rem; color: #999;">
            🤖 Boletín generado automáticamente por el Sistema de Vigilancia Epidemiológica
        </p>
    </div>
</div>
""")

    return "\n".join(html_parts)

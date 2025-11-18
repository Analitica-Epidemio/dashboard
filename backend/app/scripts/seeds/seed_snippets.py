"""
Seed de snippets para boletines epidemiológicos
"""

from datetime import datetime

from app.core.database import get_session
from app.domains.boletines.models import BoletinSnippet


def seed_snippets():
    """Crea snippets iniciales para boletines"""
    db = next(get_session())

    snippets_data = [
        # Portada
        {
            "codigo": "portada",
            "nombre": "Portada del Boletín",
            "descripcion": "Portada estándar con título y período",
            "categoria": "estructura",
            "template": """
<div class="boletin-portada" style="text-align: center; padding: 2rem;">
    <h1 style="font-size: 2rem; margin-bottom: 1rem;">Boletín Epidemiológico</h1>
    <h2 style="font-size: 1.5rem; color: #666;">Semana Epidemiológica {{ semana }} / {{ anio }}</h2>
    <p style="margin-top: 2rem;">Período: {{ fecha_inicio }} - {{ fecha_fin }}</p>
    <p style="margin-top: 1rem; font-weight: bold;">Provincia del Chubut</p>
    <p>Sistema de Vigilancia Epidemiológica</p>
</div>
            """,
            "variables_schema": {
                "semana": "number",
                "anio": "number",
                "fecha_inicio": "string",
                "fecha_fin": "string"
            },
            "condiciones": None,
            "orden": 1
        },

        # Introducción
        {
            "codigo": "introduccion",
            "nombre": "Introducción del Boletín",
            "descripcion": "Párrafo introductorio estándar",
            "categoria": "estructura",
            "template": """
<div class="boletin-introduccion">
    <h2>Introducción</h2>
    <p>
        El presente boletín epidemiológico corresponde a la Semana Epidemiológica {{ semana }} del año {{ anio }},
        abarcando el período desde {{ fecha_inicio }} hasta {{ fecha_fin }}.
    </p>
    <p>
        En este informe se presenta el análisis de {{ num_eventos }} eventos de notificación obligatoria
        detectados en la provincia del Chubut durante el período mencionado.
    </p>
</div>
            """,
            "variables_schema": {
                "semana": "number",
                "anio": "number",
                "fecha_inicio": "string",
                "fecha_fin": "string",
                "num_eventos": "number"
            },
            "condiciones": None,
            "orden": 2
        },

        # Evento en crecimiento
        {
            "codigo": "evento_crecimiento",
            "nombre": "Análisis de Evento en Crecimiento",
            "descripcion": "Template para evento con incremento de casos",
            "categoria": "evento",
            "template": """
<div class="boletin-evento evento-crecimiento">
    <h2>{{ evento_nombre }}</h2>
    <p><strong>Grupo:</strong> {{ grupo_nombre }}</p>

    <div class="resumen-casos" style="background: #fff3cd; padding: 1rem; border-radius: 4px; margin: 1rem 0;">
        <p><strong>⚠️ Incremento de casos detectado</strong></p>
        <p>Casos en período actual: <strong>{{ casos_actuales }}</strong></p>
        <p>Casos en período anterior: {{ casos_anteriores }}</p>
        <p>Cambio: <strong style="color: #d9534f;">+{{ diferencia_porcentual }}%</strong> ({{ diferencia_absoluta | abs }} casos más)</p>
    </div>

    <p>
        Durante el período analizado se registraron {{ casos_actuales }} casos de {{ evento_nombre }},
        lo que representa un incremento del {{ diferencia_porcentual }}% respecto al período anterior
        ({{ casos_anteriores }} casos). Este aumento requiere continuar con las medidas de vigilancia epidemiológica.
    </p>
</div>
            """,
            "variables_schema": {
                "evento_nombre": "string",
                "grupo_nombre": "string",
                "casos_actuales": "number",
                "casos_anteriores": "number",
                "diferencia_absoluta": "number",
                "diferencia_porcentual": "number"
            },
            "condiciones": {"tipo_cambio": "crecimiento"},
            "orden": 10
        },

        # Evento en decrecimiento
        {
            "codigo": "evento_decrecimiento",
            "nombre": "Análisis de Evento en Decrecimiento",
            "descripcion": "Template para evento con disminución de casos",
            "categoria": "evento",
            "template": """
<div class="boletin-evento evento-decrecimiento">
    <h2>{{ evento_nombre }}</h2>
    <p><strong>Grupo:</strong> {{ grupo_nombre }}</p>

    <div class="resumen-casos" style="background: #d4edda; padding: 1rem; border-radius: 4px; margin: 1rem 0;">
        <p><strong>✓ Disminución de casos detectada</strong></p>
        <p>Casos en período actual: <strong>{{ casos_actuales }}</strong></p>
        <p>Casos en período anterior: {{ casos_anteriores }}</p>
        <p>Cambio: <strong style="color: #5cb85c;">{{ diferencia_porcentual }}%</strong> ({{ diferencia_absoluta | abs }} casos menos)</p>
    </div>

    <p>
        Durante el período analizado se registraron {{ casos_actuales }} casos de {{ evento_nombre }},
        lo que representa una disminución del {{ diferencia_porcentual | abs }}% respecto al período anterior
        ({{ casos_anteriores }} casos). Esta tendencia es favorable y debe mantenerse mediante las acciones preventivas vigentes.
    </p>
</div>
            """,
            "variables_schema": {
                "evento_nombre": "string",
                "grupo_nombre": "string",
                "casos_actuales": "number",
                "casos_anteriores": "number",
                "diferencia_absoluta": "number",
                "diferencia_porcentual": "number"
            },
            "condiciones": {"tipo_cambio": "decrecimiento"},
            "orden": 11
        },

        # Conclusión
        {
            "codigo": "conclusion",
            "nombre": "Conclusión del Boletín",
            "descripcion": "Cierre estándar del boletín",
            "categoria": "estructura",
            "template": """
<div class="boletin-conclusion">
    <h2>Conclusión</h2>
    <p>
        El análisis de la Semana Epidemiológica {{ semana }} del {{ anio }} muestra la situación
        epidemiológica actual de la provincia del Chubut. Se recomienda mantener las medidas de
        vigilancia y control, así como reforzar las acciones de prevención en aquellos eventos
        que presentaron incremento de casos.
    </p>
    <p>
        El Sistema de Vigilancia Epidemiológica continuará monitoreando la evolución de todos
        los eventos de notificación obligatoria.
    </p>
</div>
            """,
            "variables_schema": {
                "semana": "number",
                "anio": "number"
            },
            "condiciones": None,
            "orden": 100
        },

        # Footer
        {
            "codigo": "footer",
            "nombre": "Pie de Página",
            "descripcion": "Footer estándar con información de contacto",
            "categoria": "estructura",
            "template": """
<div class="boletin-footer" style="margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #ccc;">
    <hr>
    <p style="text-align: center; color: #666; font-size: 0.9rem;">
        <em>Boletín Epidemiológico - Provincia del Chubut</em><br>
        Sistema de Vigilancia Epidemiológica<br>
        Ministerio de Salud - Provincia del Chubut<br>
        Generado: {{ fecha_generacion }}
    </p>
</div>
            """,
            "variables_schema": {
                "fecha_generacion": "string"
            },
            "condiciones": None,
            "orden": 999
        },
    ]

    # Verificar si ya existen snippets
    existing = db.query(BoletinSnippet).all()

    if existing:
        print(f"⚠️  Ya existen {len(existing)} snippets. Saltando seed.")
        return

    # Crear snippets
    now = datetime.utcnow()
    for snippet_data in snippets_data:
        snippet_data['created_at'] = now
        snippet_data['updated_at'] = now
        snippet = BoletinSnippet(**snippet_data)
        db.add(snippet)

    db.commit()
    print(f"✓ Creados {len(snippets_data)} snippets de boletines")


def run_seed():
    """Ejecuta el seed"""
    seed_snippets()


if __name__ == "__main__":
    run_seed()

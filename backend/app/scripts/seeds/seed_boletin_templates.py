"""
Script para crear templates de boletines de ejemplo en la base de datos
"""

import asyncio
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_engine
from app.domains.boletines.models import BoletinTemplate

# Full HTML content for the bulletin (from reportes-2/page.tsx)
BOLETIN_HTML_CONTENT = """
<p style="text-align: center"><strong>Año 2025 SE 10</strong></p>

<p style="text-align: right"><strong>Este boletín es el resultado de la información proporcionada de manera sistemática por parte de los efectores de las cuatro Unidades de Gestión Descentralizadas (UGD) que conforman la provincia de Chubut (Norte, Noroeste, Noreste y Sur), de los laboratorios provinciales de referencia, los referentes jurisdiccionales de vigilancia clínica y laboratorio y de los programas nacionales y provinciales de control, que colaboran en la configuración, gestión y usos de la información l SNVS 2.0.</strong></p>

<p style="text-align: center"><strong>Esta publicación de periodicidad semanal es elaborada por la Residencia de Epidemiología.</strong></p>

<p style="text-align: center"><strong>En este boletín se muestran los eventos agrupados notificados hasta SE 09 del año 2025 (hasta el 02/03/2025) y los eventos de notificación nominal hasta la SE 10 del año 2025 (hasta el 09/03/2025).</strong></p>

<p style="text-align: center"><strong>PUBLICACIÓN SEMANA EPIDEMIOLÓGICA 10</strong></p>
<p style="text-align: center"><strong>(03 de marzo al 09 de marzo de 2025)</strong></p>

<h2>AUTORIDADES PROVINCIALES</h2>

<p><strong>Dirección Provincial de Patologías Prevalentes y Epidemiología</strong>: Mariela Brito</p>
<p><strong>Departamento Provincial de Zooantroponosis:</strong> Alejandra Sandoval</p>
<p><strong>Departamento Provincial de Control de Enfermedades Inmunoprevenibles:</strong> Daniela Carreras</p>
<p><strong>Departamento de supervisión de actividades epidemiológicas en terreno:</strong> Alejandra Saavedra</p>
<p><strong>Departamento Laboratorial de Epidemiología:</strong> Sebastián Podestá</p>
<p><strong>Área de Vigilancia Epidemiológica:</strong> Julieta D'Andrea y Paula Martínez</p>

<h2>AUTORÍA DE ESTE BOLETÍN</h2>

<p>Este boletín está elaborado por residentes de epidemiología.</p>
<p><strong>Residentes:</strong> Adrián Tolaba, Clarisa López, Marina Westtein, Valerya Ortega, Yesica Torres.</p>
<p><strong>Jefatura de Residencia</strong>: Lis Vitorio</p>
<p><strong>Coordinación de Residencia:</strong> Julieta Levite</p>

<h2 style="text-align: center">EVENTOS DE NOTIFICACIÓN OBLIGATORIA (ENOs) – Ley N° 15465 – Provincia del Chubut</h2>

<p style="text-align: center"><strong>Tabla N°1. Casos confirmados notificados en SNVS 2.0 más frecuentes en residentes de la Provincia del Chubut en las últimas cuatro semanas. Período SE 06 - SE 09 2025</strong></p>

<table>
  <thead>
    <tr>
      <th>Evento</th>
      <th>SE 06</th>
      <th>SE 07</th>
      <th>SE 08</th>
      <th>SE 09</th>
      <th>Total</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Diarrea</td>
      <td>245</td>
      <td>268</td>
      <td>251</td>
      <td>232</td>
      <td>996</td>
    </tr>
    <tr>
      <td>Neumonía</td>
      <td>42</td>
      <td>38</td>
      <td>45</td>
      <td>41</td>
      <td>166</td>
    </tr>
    <tr>
      <td>Bronquiolitis</td>
      <td>28</td>
      <td>31</td>
      <td>24</td>
      <td>19</td>
      <td>102</td>
    </tr>
    <tr>
      <td>Varicela</td>
      <td>15</td>
      <td>12</td>
      <td>18</td>
      <td>14</td>
      <td>59</td>
    </tr>
    <tr>
      <td>Sífilis</td>
      <td>8</td>
      <td>11</td>
      <td>9</td>
      <td>7</td>
      <td>35</td>
    </tr>
  </tbody>
</table>

<p><em>*Incluye población general y personas gestantes.</em></p>
<p><em>No se consideran los eventos respiratorios ya que forman parte del desarrollo de este boletín provincial. Fuente: SNVS2.0 –SISA</em></p>

<div data-type="page-break"></div>

<p style="text-align: center"><strong>El análisis de los Eventos agrupados relacionados a la vigilancia de infecciones respiratorias agudas se realizó con los datos de aquellos establecimientos que notificaron un 80% de las semanas epidemiológicas del año 2025.</strong></p>

<p style="text-align: center"><strong>La notificación oportuna de los datos en SISA, permite optimizar la gestión de la información, la evaluación de la actividad y la toma de decisiones.</strong></p>

<h2 style="text-align: center">VIGILANCIA DE INFECCIONES RESPIRATORIAS AGUDAS</h2>

<h3>ENFERMEDAD TIPO INFLUENZA (ETI)</h3>

<div data-type="dynamic-chart" data-query-type="corredor_ira" data-chart-type="corridor" data-title="Gráfico Nº1. Corredor endémico semanal de ETI. Provincia del Chubut. SE 1-8 Año 2025. N= 613" data-height="400"></div>

<p>El corredor endémico de ETI en las primeras semanas del 2025 se ubica entre zona de seguridad y alerta.</p>

<h3>NEUMONÍA</h3>

<div data-type="dynamic-chart" data-query-type="corredor_ira" data-chart-type="corridor" data-title="Gráfico Nº2. Corredor endémico semanal de Neumonía. Provincia del Chubut. SE 1-8 Año 2025. N=134" data-height="400"></div>

<p>El corredor endémico de neumonía en las primeras semanas del 2025 alterna entre alerta y seguridad, la SE 07 se ubica en brote.</p>

<h3>BRONQUIOLITIS</h3>

<div data-type="dynamic-chart" data-query-type="corredor_ira" data-chart-type="corridor" data-title="Gráfico Nº3. Corredor endémico semanal de Bronquiolitis. Provincia del Chubut. SE 1-8 Año 2025. N=77" data-height="400"></div>

<p>El corredor endémico de bronquiolitis durante las primeras semanas del 2025 se ubica en zona de brote.</p>

<div data-type="dynamic-chart" data-query-type="virus_respiratorios" data-chart-type="bar" data-title="Grafico Nº 4. Casos de ETI, Neumonía y Bronquiolitis por grupo etario. Provincia del Chubut. SE 1-8 Año 2025. N= 824" data-height="400"></div>

<p>A la SE 8 del año 2025 el mayor número de casos de ETI se registra en el grupo etario de 45 a 64 años con el 22% (134/613*100) de los casos, el mayor número de casos de Neumonía se ubica en los grupos de personas mayores a 65 años con el 41% (55/134*100) y de Bronquiolitis en el grupo de niños menores de 6 meses con el 55% (42/77*100).</p>

<h3>VIGILANCIA DE VIRUS RESPIRATORIOS EN INTERNADOS Y/O FALLECIDOS POR IRA</h3>

<p>A la semana 9 del año 2025 se notificaron 53 internados en el evento "Internados y/o fallecido por COVID o IRA", de éstos se obtuvo 3 muestras positivas que corresponden a SARS-COV2, y 1 muestra positiva para Influenza A.</p>

<div data-type="dynamic-chart" data-query-type="virus_respiratorios" data-chart-type="line" data-title="Gráfico N°5. Internado por IRA según agente etiológico detectado por semana epidemiologica. Provincia del Chubut. SE 1/2024 a SE 9/2025. N=271" data-height="400"></div>

<p style="text-align: center"><strong>Tabla N°2. Internado por IRA según agente etiológico y según grupo etario. Provincia del Chubut. SE 1 a 9. Año 2025. N=4</strong></p>

<table>
  <thead>
    <tr>
      <th>Agente Etiológico</th>
      <th>0-5 años</th>
      <th>6-17 años</th>
      <th>18-64 años</th>
      <th>65+ años</th>
      <th>Total</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>SARS-CoV-2</td>
      <td>0</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>3</td>
    </tr>
    <tr>
      <td>Influenza A</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
    </tr>
  </tbody>
</table>

<h3 style="text-align: center">VIGILANCIA DE INFLUENZA EN INTERNADOS Y/O AMBULATORIOS</h3>

<p style="text-align: center"><strong>Tabla N° 3. Casos positivos totales de virus de influenza según tipificación en ambulatorios e internados. Provincia del Chubut. Año 2025 SE 1 a SE 9. N=1</strong></p>

<table>
  <thead>
    <tr>
      <th>Tipo/Subtipo</th>
      <th>Ambulatorios</th>
      <th>Internados</th>
      <th>Total</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Influenza A - sin subtipificar</td>
      <td>0</td>
      <td>1</td>
      <td>1</td>
    </tr>
  </tbody>
</table>

<p>Hasta la semana epidemiológica 9 del año 2025 se identificó 1 caso para el evento Influenza A-sin subtipificar, correspondiente a un varón en el grupo etario de 10 a 14 años en la SE 8.</p>

<h3>VIGILANCIA DE INTERNACIONES POR INFECCIONES RESPIRATORIAS AGUDAS</h3>

<p>La modalidad de notificación agrupada de vigilancia de internaciones por Infecciones respiratorias agudas en SNVS 2.0 se realiza una vez por semana con el parte de internados de los miércoles. La siguiente tabla representa la dotación de camas reportadas por los hospitales de la provincia:</p>

<p style="text-align: center"><strong>Tabla N°4. Dotación de camas. Provincia de Chubut. SE 9. Año 2025. N=387</strong></p>

<table>
  <thead>
    <tr>
      <th>Servicio</th>
      <th>Dotación</th>
      <th>Ocupadas</th>
      <th>Disponibles</th>
      <th>% Ocupación</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Internación General Adultos</td>
      <td>180</td>
      <td>142</td>
      <td>38</td>
      <td>78.9%</td>
    </tr>
    <tr>
      <td>Internación Pediátrica</td>
      <td>85</td>
      <td>62</td>
      <td>23</td>
      <td>72.9%</td>
    </tr>
    <tr>
      <td>UTI Adultos</td>
      <td>42</td>
      <td>38</td>
      <td>4</td>
      <td>90.5%</td>
    </tr>
    <tr>
      <td>UTI Pediátrica</td>
      <td>18</td>
      <td>14</td>
      <td>4</td>
      <td>77.8%</td>
    </tr>
    <tr>
      <td>ARM (Ventilación Mecánica)</td>
      <td>62</td>
      <td>51</td>
      <td>11</td>
      <td>82.3%</td>
    </tr>
  </tbody>
</table>

<p>Durante la SE 09 de 2025, se observa una disminución en pacientes en internación general adultos por IRA y en pediátricos en internación por IRA, un aumento en pacientes UTI y ARM adultos, y el resto de los servicios permanecieron sin cambios respecto a la semana anterior.</p>

<div data-type="page-break"></div>

<h2 style="text-align: center">INTOXICACIÓN POR MONÓXIDO DE CARBONO (CO)</h2>

<div data-type="dynamic-chart" data-query-type="intoxicacion_co" data-chart-type="bar" data-title="Gráfico N°5. Casos confirmados de intoxicación por monóxido de carbono. Provincia del Chubut. SE 1-9 Año 2025 N=7" data-height="400"></div>

<p>A la SE 9 del año 2025 se notificaron 7 casos confirmados de Intoxicación por monóxido de carbono. Se observa un aumento del 40% de los casos notificados en el año 2025 comparando con 2024. La mayor tasa de incidencia la presenta UGD Norte (2,8 x100.000 hab.)</p>

<p>Desde la SE 1 a la SE 9 de 2025 se notificaron 7 casos confirmados para este evento, 3 casos corresponden a la UGD Norte (AP Norte), 2 a Noroeste (AP Esquel), 1 a Noreste (AP Trelew) y 1 a Sur (AP Comodoro Rivadavia).</p>
"""

# Template de Boletín Semanal
TEMPLATE_BOLETIN_SEMANAL = {
    "name": "Boletín Epidemiológico Semanal",
    "description": "Plantilla completa para boletines semanales con análisis de ENOs, vigilancia IRA y capacidad hospitalaria",
    "category": "semanal",
    "content": BOLETIN_HTML_CONTENT,
    "layout": {
        "type": "grid",
        "columns": 12,
        "row_height": 40,
        "margin": [10, 10]
    },
    "cover": {
        "enabled": True,
        "title": "Boletín Epidemiológico",
        "subtitle": "Ministerio de Salud Pública - Provincia del Chubut",
        "footer": "Dirección de Epidemiología"
    },
    "widgets": [],
    "global_filters": {
        "temporal": {
            "enabled": True,
            "default_period": "week"
        },
        "geografico": {
            "enabled": True,
            "level": "provincia"
        }
    },
    "is_public": True,
    "is_system": True
}

# Template de Reporte de Brote
TEMPLATE_REPORTE_BROTE = {
    "name": "Reporte de Brote",
    "description": "Plantilla rápida para reportes de brotes con visualizaciones de distribución geográfica",
    "category": "brote",
    "content": "<h1>Reporte de Brote</h1><p>Comienza a escribir tu reporte aquí...</p>",
    "layout": {
        "type": "grid",
        "columns": 12,
        "row_height": 40,
        "margin": [10, 10]
    },
    "cover": {
        "enabled": True,
        "title": "Reporte de Brote",
        "subtitle": "Alerta Epidemiológica"
    },
    "widgets": [],
    "global_filters": {
        "temporal": {
            "enabled": True
        }
    },
    "is_public": True,
    "is_system": True
}

# Template de Análisis de Tendencias
TEMPLATE_ANALISIS_TENDENCIAS = {
    "name": "Análisis de Tendencias",
    "description": "Plantilla para análisis de tendencias temporales y comparación de períodos",
    "category": "tendencias",
    "content": "<h1>Análisis de Tendencias Epidemiológicas</h1><p>Comienza a escribir tu análisis aquí...</p>",
    "layout": {
        "type": "grid",
        "columns": 12,
        "row_height": 40,
        "margin": [10, 10]
    },
    "cover": {
        "enabled": True,
        "title": "Análisis de Tendencias Epidemiológicas",
        "subtitle": "Comparación de Períodos"
    },
    "widgets": [],
    "global_filters": {
        "temporal": {
            "enabled": True,
            "allow_comparison": True
        }
    },
    "is_public": True,
    "is_system": True
}

TEMPLATES = [
    TEMPLATE_BOLETIN_SEMANAL,
    TEMPLATE_REPORTE_BROTE,
    TEMPLATE_ANALISIS_TENDENCIAS
]


async def seed_templates():
    """Crear o actualizar templates de ejemplo en la base de datos"""
    async with AsyncSession(async_engine) as db:
        print("🌱 Seeding boletin templates...")

        for template_data in TEMPLATES:
            # Check if template already exists
            stmt = select(BoletinTemplate).where(
                BoletinTemplate.name == template_data["name"]
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                print(f"   🔄 Updating template: {template_data['name']}")
                # Update existing template
                for key, value in template_data.items():
                    setattr(existing, key, value)
            else:
                # Create new template
                template = BoletinTemplate(**template_data)
                db.add(template)
                print(f"   ✅ Created template: {template_data['name']}")

        await db.commit()
        print("✨ Seeding completed!")


if __name__ == "__main__":
    asyncio.run(seed_templates())

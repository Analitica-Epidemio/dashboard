"""
Seed de configuración de charts del dashboard.
Basado en los charts del sistema epidemiologia_chubut.
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlmodel import select

from app.features.dashboard.models import DashboardChart

# Configuración de charts basados en el sistema Chubut
DASHBOARD_CHARTS = [
    {
        "codigo": "curva-epidemiologica",
        "nombre": "Curva Epidemiológica",
        "descripcion": "Casos por semana epidemiológica",
        "funcion_procesamiento": "curva_epidemiologica",
        "condiciones_display": None,  # Siempre visible
        "tipo_visualizacion": "line",
        "configuracion_chart": {"height": 300},
        "orden": 1,
        "activo": True
    },
    {
        "codigo": "corredor-endemico",
        "nombre": "Corredor Endémico",
        "descripcion": "Comparación con histórico",
        "funcion_procesamiento": "corredor_endemico",
        "condiciones_display": None,
        "tipo_visualizacion": "area",
        "configuracion_chart": {"height": 300},
        "orden": 2,
        "activo": True
    },
    {
        "codigo": "piramide-poblacional",
        "nombre": "Pirámide Poblacional",
        "descripcion": "Distribución por edad y sexo",
        "funcion_procesamiento": "piramide_poblacional",
        "condiciones_display": None,
        "tipo_visualizacion": "d3_pyramid",
        "configuracion_chart": {"height": 500},
        "orden": 3,
        "activo": True
    },
    {
        "codigo": "mapa-geografico",
        "nombre": "Mapa Geográfico",
        "descripcion": "Visualización geográfica de casos por departamento",
        "funcion_procesamiento": "mapa_geografico",
        "condiciones_display": None,
        "tipo_visualizacion": "mapa",
        "configuracion_chart": {"height": 500},
        "orden": 4,
        "activo": True
    },
    {
        "codigo": "totales-historicos",
        "nombre": "Totales Históricos",
        "descripcion": "Evolución anual de casos",
        "funcion_procesamiento": "totales_historicos",
        "condiciones_display": None,
        "tipo_visualizacion": "bar",
        "configuracion_chart": {"height": 300},
        "orden": 5,
        "activo": True
    },
    {
        "codigo": "torta-sexo",
        "nombre": "Distribución por Sexo",
        "descripcion": "Proporción de casos por sexo",
        "funcion_procesamiento": "torta_sexo",
        "condiciones_display": None,
        "tipo_visualizacion": "pie",
        "configuracion_chart": {"height": 200},
        "orden": 6,
        "activo": True
    },
    {
        "codigo": "casos-edad",
        "nombre": "Casos por Edad",
        "descripcion": "Distribución por grupos etarios",
        "funcion_procesamiento": "casos_edad",
        "condiciones_display": None,
        "tipo_visualizacion": "bar",
        "configuracion_chart": {"height": 300},
        "orden": 7,
        "activo": True
    },
    {
        "codigo": "intento-suicidio",
        "nombre": "Análisis Intentos Suicidio",
        "descripcion": "Métodos y factores",
        "funcion_procesamiento": "intento_suicidio",
        "condiciones_display": {"grupo_codigos": ["lesiones-intencionales"]},
        "tipo_visualizacion": "bar",
        "configuracion_chart": {"height": 300},
        "orden": 8,
        "activo": True
    },
    {
        "codigo": "rabia-animal",
        "nombre": "Casos Rabia Animal",
        "descripcion": "Distribución por especie",
        "funcion_procesamiento": "rabia_animal",
        "condiciones_display": {"grupo_codigos": ["rabia"]},
        "tipo_visualizacion": "bar",
        "configuracion_chart": {"height": 300},
        "orden": 9,
        "activo": True
    },
    {
        "codigo": "proporcion-ira",
        "nombre": "Proporción IRA",
        "descripcion": "Distribución de infecciones respiratorias agudas",
        "funcion_procesamiento": "proporcion_ira",
        "condiciones_display": {"grupo_codigos": ["infecciones-respiratorias-agudas"]},
        "tipo_visualizacion": "pie",
        "configuracion_chart": {"height": 400},
        "orden": 10,
        "activo": True
    }
]


def main():
    """
    Crea los charts del dashboard en la base de datos.
    """
    print("\n📊 Seeding Dashboard Charts...")
    
    # Obtener la URL de la base de datos
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://epidemiologia_user:epidemiologia_password@db:5432/epidemiologia_db"
    )
    
    # Cambiar postgresql+asyncpg:// por postgresql:// para usar psycopg2 síncrono
    if "postgresql+asyncpg" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace(
            "postgresql+asyncpg://", "postgresql://"
        )
    
    # Crear engine y sesión
    engine = create_engine(DATABASE_URL)
    
    with Session(engine) as session:
        created_count = 0
        updated_count = 0
        
        for chart_data in DASHBOARD_CHARTS:
            # Check if chart already exists
            stmt = select(DashboardChart).where(DashboardChart.codigo == chart_data["codigo"])
            existing = session.execute(stmt).scalar_one_or_none()
            
            if existing:
                # Update existing chart
                existing.nombre = chart_data["nombre"]
                existing.descripcion = chart_data["descripcion"]
                existing.funcion_procesamiento = chart_data["funcion_procesamiento"]
                existing.condiciones_display = chart_data["condiciones_display"]
                existing.tipo_visualizacion = chart_data["tipo_visualizacion"]
                existing.configuracion_chart = chart_data["configuracion_chart"]
                existing.orden = chart_data["orden"]
                existing.activo = chart_data["activo"]
                existing.updated_at = datetime.now()
                updated_count += 1
                print(f"  ↻  Chart {chart_data['codigo']} actualizado")
            else:
                # Create new chart
                chart = DashboardChart(
                    codigo=chart_data["codigo"],
                    nombre=chart_data["nombre"],
                    descripcion=chart_data["descripcion"],
                    funcion_procesamiento=chart_data["funcion_procesamiento"],
                    condiciones_display=chart_data["condiciones_display"],
                    tipo_visualizacion=chart_data["tipo_visualizacion"],
                    configuracion_chart=chart_data["configuracion_chart"],
                    orden=chart_data["orden"],
                    activo=chart_data["activo"],
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                session.add(chart)
                created_count += 1
                print(f"  ✅ Chart {chart.codigo} creado")
        
        session.commit()
        print(f"\n✅ {created_count} Dashboard Charts creados, {updated_count} actualizados")


if __name__ == "__main__":
    # Para testing directo
    main()
#!/usr/bin/env python3
"""
Script para reprocesar el CSV de Dengue con el logging mejorado.
Usa el mismo procesador que el sistema, pero ejecutándolo de forma síncrona.
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.features.procesamiento_archivos.processors.simple_processor import create_processor


def main():
    """Procesa el CSV de Dengue."""

    # Ruta al CSV (dentro del contenedor Docker)
    csv_path = Path('/app/Meningitis 2024 y 2023.xlsx - Hoja 1(1).csv')

    if not csv_path.exists():
        print(f"❌ Archivo CSV no encontrado: {csv_path}")
        return

    print(f"\n{'='*80}")
    print(f"🔄 REPROCESAMIENTO DE CSV CON LOGGING MEJORADO")
    print(f"{'='*80}\n")
    print(f"📄 Archivo: {csv_path}")
    print(f"📊 Tamaño: {csv_path.stat().st_size / 1024 / 1024:.2f} MB\n")

    # Conectar a la base de datos
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://epidemiologia_user:epidemiologia_password@localhost:5433/epidemiologia_db"
    )
    if "postgresql+asyncpg" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    print(f"🔌 Conectando a la base de datos...\n")
    engine = create_engine(DATABASE_URL, echo=False)

    with Session(engine) as session:
        # Callback para progreso
        def update_progress(percentage: int, message: str):
            print(f"   [{percentage:3d}%] {message}")

        # Crear procesador
        print("🏗️  Creando procesador...")
        processor = create_processor(session, update_progress)

        # Procesar archivo
        print("🚀 Iniciando procesamiento...\n")
        start_time = datetime.now()

        try:
            result = processor.process_file(csv_path, sheet_name=None)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            print(f"\n{'='*80}")
            print(f"📊 RESULTADOS DEL PROCESAMIENTO")
            print(f"{'='*80}\n")
            print(f"Estado: {result['status']}")
            print(f"Tiempo: {duration:.2f} segundos")
            print(f"Filas totales: {result['total_rows']}")
            print(f"Filas procesadas: {result['processed_rows']}")
            print(f"\nEntidades creadas:")
            print(f"  - Ciudadanos: {result.get('ciudadanos_created', 0)}")
            print(f"  - Eventos: {result.get('eventos_created', 0)}")
            print(f"  - Diagnósticos: {result.get('diagnosticos_created', 0)}")

            if result.get('errors'):
                print(f"\n⚠️  Errores encontrados: {len(result['errors'])}")
                for i, error in enumerate(result['errors'][:5], 1):
                    print(f"  {i}. {error}")
                if len(result['errors']) > 5:
                    print(f"  ... y {len(result['errors']) - 5} más")

            print(f"\n{'='*80}\n")

        except Exception as e:
            print(f"\n❌ ERROR durante el procesamiento:")
            print(f"   {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()

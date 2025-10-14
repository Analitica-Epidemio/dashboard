#!/usr/bin/env python3
"""
Script para debuggear por qué no se importan muestras.
"""
import sys
from pathlib import Path
sys.path.append('/app')

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import pandas as pd
import os

from app.features.procesamiento_archivos.processors.bulk_processors.salud import SaludBulkProcessor
from app.features.procesamiento_archivos.processors.core.base_processor import ProcessingContext
from app.features.procesamiento_archivos.processors.core.columns import Columns
from app.domains.eventos_epidemiologicos.eventos.models import Evento
from sqlalchemy import select, func

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://epidemiologia_user:epidemiologia_password@db:5432/epidemiologia_db')
if 'postgresql+asyncpg' in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')

engine = create_engine(DATABASE_URL)

with Session(engine) as session:
    print('=== DEBUG: Importación de Muestras ===\n')

    # Cargar CSV
    df = pd.read_csv('/app/Meningitis 2024 y 2023.xlsx - Hoja 1(1).csv', low_memory=False)
    print(f'Total filas CSV: {len(df)}')

    # Filtrar muestras
    muestras_df = df[
        df[Columns.ID_SNVS_MUESTRA].notna()
        | df[Columns.MUESTRA].notna()
        | df[Columns.FECHA_ESTUDIO].notna()
    ]
    print(f'Filas con datos de muestra: {len(muestras_df)}')

    # Verificar eventos en BD
    print(f'\nEventos en BD: {session.execute(select(func.count()).select_from(Evento)).scalar()}')

    # Crear processor
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    context = ProcessingContext(
        session=session,
        progress_callback=None,
        batch_size=1000,
    )

    processor = SaludBulkProcessor(context, logger)

    # Debug detallado
    print('\n=== Detalles antes de procesar ===')

    # Simular el procesamiento manualmente
    muestras_df = df[
        df[Columns.ID_SNVS_MUESTRA].notna()
        | df[Columns.MUESTRA].notna()
        | df[Columns.FECHA_ESTUDIO].notna()
    ].copy()

    print(f'Muestras df size: {len(muestras_df)}')
    print(f'Eventos únicos en muestras: {muestras_df[Columns.IDEVENTOCASO].nunique()}')
    print(f'ID_SNVS_MUESTRA notna: {muestras_df[Columns.ID_SNVS_MUESTRA].notna().sum()}')
    print(f'MUESTRA notna: {muestras_df[Columns.MUESTRA].notna().sum()}')

    # Procesar muestras
    print('\n=== Procesando muestras ===')
    result = processor.bulk_upsert_muestras_eventos(df)

    print(f'\n=== Resultado ===')
    print(f'Insertadas: {result.inserted_count}')
    print(f'Actualizadas: {result.updated_count}')
    print(f'Saltadas: {result.skipped_count}')
    print(f'Errores: {len(result.errors)}')
    if result.errors:
        for error in result.errors[:5]:
            print(f'  - {error}')

    # Commit para persistir
    session.commit()

    # Verificar en BD
    from app.domains.atencion_medica.salud_models import MuestraEvento
    total_muestras = session.execute(select(func.count()).select_from(MuestraEvento)).scalar()
    print(f'\nMuestras en BD después de procesar: {total_muestras}')

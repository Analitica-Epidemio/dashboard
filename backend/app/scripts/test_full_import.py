#!/usr/bin/env python3
"""
Script para probar la importación completa de muestras siguiendo el flujo correcto.
"""
import sys
sys.path.append('/app')

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
import pandas as pd
import os
import logging

from app.features.procesamiento_archivos.processors.bulk_processors.main_processor import MainBulkProcessor
from app.features.procesamiento_archivos.processors.core.base_processor import ProcessingContext
from app.domains.eventos_epidemiologicos.eventos.models import Evento
from app.domains.atencion_medica.salud_models import MuestraEvento, Muestra

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://epidemiologia_user:epidemiologia_password@db:5432/epidemiologia_db')
if 'postgresql+asyncpg' in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')

engine = create_engine(DATABASE_URL)

with Session(engine) as session:
    logger.info('=== TEST: Importación Completa con Muestras ===\n')

    # Cargar CSV
    df = pd.read_csv('/app/Meningitis 2024 y 2023.xlsx - Hoja 1(1).csv', low_memory=False)
    logger.info(f'Total filas CSV: {len(df)}')

    # Crear context
    context = ProcessingContext(
        session=session,
        progress_callback=None,
        batch_size=1000,
    )

    # Crear processor principal
    main_processor = MainBulkProcessor(context, logger)

    # Procesar todo en orden correcto
    logger.info('\n=== Procesando en orden correcto ===')
    results = main_processor.process_all(df)

    # Commit para persistir
    session.commit()

    # Verificar resultados
    logger.info('\n=== Verificación Final ===')
    total_eventos = session.execute(select(func.count()).select_from(Evento)).scalar()
    total_muestras = session.execute(select(func.count()).select_from(MuestraEvento)).scalar()
    total_tipos_muestra = session.execute(select(func.count()).select_from(Muestra)).scalar()

    logger.info(f'Eventos en BD: {total_eventos}')
    logger.info(f'Tipos de muestra (catálogo): {total_tipos_muestra}')
    logger.info(f'Muestras eventos en BD: {total_muestras}')

    if total_muestras == 0:
        logger.error('❌ NO SE IMPORTARON MUESTRAS!')
    else:
        logger.info(f'✅ {total_muestras} muestras importadas correctamente')

#!/usr/bin/env python3
"""
Script de validación de importación de eventos.
Compara los datos del CSV original con los datos en la base de datos.
"""
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

import pandas as pd
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.domains.eventos_epidemiologicos.eventos.models import Evento, TipoEno
from app.domains.sujetos_epidemiologicos.ciudadanos_models import Ciudadano
from app.domains.territorio.establecimientos_models import Establecimiento


def parse_date(date_val):
    """Parsear fecha del CSV a objeto date."""
    if pd.isna(date_val) or not str(date_val).strip():
        return None

    # Intentar varios formatos
    for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']:
        try:
            return datetime.strptime(str(date_val).strip(), fmt).date()
        except:
            continue
    return None


def validate_evento_fields(csv_row: pd.Series, db_evento: Evento, db_ciudadano: Ciudadano = None) -> Dict[str, Any]:
    """Valida que los campos del evento en DB coincidan con el CSV."""

    validations = {
        'id_evento_caso': {
            'csv': int(csv_row['IDEVENTOCASO']),
            'db': db_evento.id_evento_caso,
            'match': int(csv_row['IDEVENTOCASO']) == db_evento.id_evento_caso
        }
    }

    # Validar código ciudadano si existe
    if 'CODIGO_CIUDADANO' in csv_row and pd.notna(csv_row['CODIGO_CIUDADANO']):
        csv_codigo = int(csv_row['CODIGO_CIUDADANO'])
        validations['codigo_ciudadano'] = {
            'csv': csv_codigo,
            'db': db_evento.codigo_ciudadano,
            'match': csv_codigo == db_evento.codigo_ciudadano
        }

    # Validar fecha_inicio_sintomas
    fecha_sintoma_csv = parse_date(csv_row.get('FECHA_INICIO_SINTOMA'))
    validations['fecha_inicio_sintomas'] = {
        'csv': fecha_sintoma_csv,
        'db': db_evento.fecha_inicio_sintomas,
        'match': fecha_sintoma_csv == db_evento.fecha_inicio_sintomas
    }

    # Validar fecha_minima_evento (calculada desde 4 columnas)
    fechas_csv = []
    for col in ['FECHA_APERTURA', 'FECHA_INICIO_SINTOMA', 'FECHA_CONSULTA', 'FTM']:
        if col in csv_row:
            fecha = parse_date(csv_row.get(col))
            if fecha:
                fechas_csv.append(fecha)

    fecha_minima_esperada = min(fechas_csv) if fechas_csv else None
    validations['fecha_minima_evento'] = {
        'csv_sources': {
            'FECHA_APERTURA': parse_date(csv_row.get('FECHA_APERTURA')),
            'FECHA_INICIO_SINTOMA': parse_date(csv_row.get('FECHA_INICIO_SINTOMA')),
            'FECHA_CONSULTA': parse_date(csv_row.get('FECHA_CONSULTA')),
            'FTM': parse_date(csv_row.get('FTM')),
        },
        'csv_calculated': fecha_minima_esperada,
        'db': db_evento.fecha_minima_evento,
        'match': fecha_minima_esperada == db_evento.fecha_minima_evento
    }

    # Validar tipo de evento
    if 'EVENTO' in csv_row and pd.notna(csv_row['EVENTO']):
        validations['tipo_evento'] = {
            'csv': str(csv_row['EVENTO']).strip(),
            'db': db_evento.tipo_eno.nombre if db_evento.tipo_eno else None,
            'db_id': db_evento.id_tipo_eno,
            'match': True  # Solo informativo, no podemos comparar directamente
        }

    # Validar clasificación
    validations['clasificacion'] = {
        'csv': csv_row.get('CLASIFICACIONMANUAL'),
        'db': db_evento.clasificacion_estrategia,
        'db_confidence': db_evento.confidence_score,
    }

    # Validar datos del ciudadano si existe
    if db_ciudadano:
        validations['ciudadano'] = {
            'nombre_csv': csv_row.get('NOMBRE'),
            'apellido_csv': csv_row.get('APELLIDO'),
            'nombre_db': db_ciudadano.nombre,
            'apellido_db': db_ciudadano.apellido,
            'match': (
                str(csv_row.get('NOMBRE', '')).strip().upper() == str(db_ciudadano.nombre or '').strip().upper() and
                str(csv_row.get('APELLIDO', '')).strip().upper() == str(db_ciudadano.apellido or '').strip().upper()
            )
        }

        # Validar documento
        if 'NUMERO_DOCUMENTO' in csv_row and pd.notna(csv_row['NUMERO_DOCUMENTO']):
            validations['documento'] = {
                'csv': int(csv_row['NUMERO_DOCUMENTO']),
                'db': db_ciudadano.numero_documento,
                'match': int(csv_row['NUMERO_DOCUMENTO']) == db_ciudadano.numero_documento
            }

    return validations


def main():
    """Ejecuta la validación."""

    # Ruta al CSV
    csv_path = '/Users/ignacio/Documents/work/epidemiologia/dashboard/backend/Meningitis 2024 y 2023.xlsx - Hoja 1(1).csv'

    if not os.path.exists(csv_path):
        print(f"❌ Archivo CSV no encontrado: {csv_path}")
        return

    print(f"\n{'='*80}")
    print(f"🔍 VALIDACIÓN DE IMPORTACIÓN DE EVENTOS")
    print(f"{'='*80}\n")
    print(f"📄 CSV: {csv_path}\n")

    # Cargar CSV
    print("📊 Cargando CSV...")
    df = pd.read_csv(csv_path)
    print(f"   Total de filas en CSV: {len(df)}")

    # Analizar eventos únicos en CSV
    eventos_unicos_csv = df['IDEVENTOCASO'].nunique()
    filas_por_evento = df.groupby('IDEVENTOCASO').size()
    eventos_con_multiples_filas = (filas_por_evento > 1).sum()

    print(f"   Eventos únicos (IDEVENTOCASO): {eventos_unicos_csv}")
    print(f"   Eventos con múltiples filas: {eventos_con_multiples_filas}")
    print(f"   Filas por evento - min: {filas_por_evento.min()}, max: {filas_por_evento.max()}, promedio: {filas_por_evento.mean():.1f}")

    # Conectar a la base de datos
    # Usar puerto 5433 que es el mapeado del contenedor Docker
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://epidemiologia_user:epidemiologia_password@localhost:5433/epidemiologia_db"
    )
    if "postgresql+asyncpg" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    print(f"\n🔌 Conectando a la base de datos...")
    engine = create_engine(DATABASE_URL)

    with Session(engine) as session:
        # Seleccionar 10 casos para validar:
        # - 5 con una sola fila
        # - 5 con múltiples filas
        casos_una_fila = filas_por_evento[filas_por_evento == 1].index.tolist()[:5]
        casos_multiples_filas = filas_por_evento[filas_por_evento > 1].index.tolist()[:5]

        casos_a_validar = casos_una_fila + casos_multiples_filas

        print(f"\n📋 Validando {len(casos_a_validar)} casos:")
        print(f"   - {len(casos_una_fila)} casos con 1 fila")
        print(f"   - {len(casos_multiples_filas)} casos con múltiples filas\n")

        resultados_validacion = []

        for i, id_evento_caso in enumerate(casos_a_validar, 1):
            print(f"\n{'─'*80}")
            print(f"CASO {i}/{len(casos_a_validar)}: ID Evento Caso = {id_evento_caso}")
            print(f"{'─'*80}")

            # Obtener todas las filas de este evento del CSV
            filas_evento = df[df['IDEVENTOCASO'] == id_evento_caso]
            num_filas = len(filas_evento)
            print(f"📊 Filas en CSV: {num_filas}")

            # Mostrar las primeras columnas clave de cada fila
            if num_filas > 1:
                print(f"\n   Desglose de filas:")
                for idx, (_, row) in enumerate(filas_evento.iterrows(), 1):
                    sintoma = row.get('SIGNO_SINTOMA', 'N/A')
                    print(f"   Fila {idx}: SIGNO_SINTOMA='{sintoma}'")

            # Buscar el evento en la base de datos
            stmt = (
                select(Evento, TipoEno, Ciudadano)
                .outerjoin(TipoEno, Evento.id_tipo_eno == TipoEno.id)
                .outerjoin(Ciudadano, Evento.codigo_ciudadano == Ciudadano.codigo_ciudadano)
                .where(Evento.id_evento_caso == id_evento_caso)
            )
            result = session.execute(stmt).first()

            if not result:
                print(f"❌ Evento NO encontrado en la base de datos")
                resultados_validacion.append({
                    'id_evento_caso': id_evento_caso,
                    'encontrado': False,
                    'num_filas_csv': num_filas
                })
                continue

            db_evento, db_tipo_eno, db_ciudadano = result
            print(f"✅ Evento encontrado en BD (id={db_evento.id})")

            # Usar la primera fila del CSV como referencia para campos del evento
            primera_fila = filas_evento.iloc[0]

            # Validar campos
            validations = validate_evento_fields(primera_fila, db_evento, db_ciudadano)

            # Mostrar resultados
            print(f"\n🔍 Validación de campos:")

            total_checks = 0
            passed_checks = 0

            for field, data in validations.items():
                if field == 'fecha_minima_evento':
                    # Caso especial para fecha_minima
                    print(f"\n   📅 {field}:")
                    print(f"      Fuentes del CSV:")
                    for col, fecha in data['csv_sources'].items():
                        print(f"        - {col}: {fecha}")
                    print(f"      Fecha calculada (min): {data['csv_calculated']}")
                    print(f"      Fecha en DB: {data['db']}")
                    match_symbol = "✅" if data['match'] else "❌"
                    print(f"      Match: {match_symbol}")
                    total_checks += 1
                    if data['match']:
                        passed_checks += 1

                elif field == 'ciudadano':
                    print(f"\n   👤 {field}:")
                    print(f"      CSV: {data['nombre_csv']} {data['apellido_csv']}")
                    print(f"      DB:  {data['nombre_db']} {data['apellido_db']}")
                    match_symbol = "✅" if data['match'] else "❌"
                    print(f"      Match: {match_symbol}")
                    total_checks += 1
                    if data['match']:
                        passed_checks += 1

                elif field == 'clasificacion':
                    print(f"\n   🏷️  {field}:")
                    print(f"      CSV: {data['csv']}")
                    print(f"      DB:  {data['db']} (confidence: {data['db_confidence']})")

                elif field == 'tipo_evento':
                    print(f"\n   📂 {field}:")
                    print(f"      CSV: {data['csv']}")
                    print(f"      DB:  {data['db']} (id: {data['db_id']})")

                elif isinstance(data, dict) and 'match' in data:
                    match_symbol = "✅" if data['match'] else "❌"
                    print(f"   {match_symbol} {field}: CSV={data['csv']} | DB={data['db']}")
                    total_checks += 1
                    if data['match']:
                        passed_checks += 1

            # Contar síntomas asociados
            num_sintomas = len(db_evento.sintomas or [])
            print(f"\n   💊 Síntomas asociados: {num_sintomas} (esperado: {num_filas} basado en filas CSV)")

            # Resumen
            print(f"\n   📊 Resumen: {passed_checks}/{total_checks} validaciones pasadas")

            resultados_validacion.append({
                'id_evento_caso': id_evento_caso,
                'encontrado': True,
                'num_filas_csv': num_filas,
                'num_sintomas_db': num_sintomas,
                'validaciones_pasadas': passed_checks,
                'validaciones_totales': total_checks,
                'porcentaje_ok': (passed_checks / total_checks * 100) if total_checks > 0 else 0
            })

        # Resumen final
        print(f"\n\n{'='*80}")
        print(f"📊 RESUMEN FINAL")
        print(f"{'='*80}\n")

        casos_encontrados = sum(1 for r in resultados_validacion if r['encontrado'])
        casos_no_encontrados = len(resultados_validacion) - casos_encontrados

        print(f"Casos validados: {len(resultados_validacion)}")
        print(f"  ✅ Encontrados en DB: {casos_encontrados}")
        print(f"  ❌ No encontrados: {casos_no_encontrados}")

        if casos_encontrados > 0:
            validaciones_totales = sum(r.get('validaciones_totales', 0) for r in resultados_validacion if r['encontrado'])
            validaciones_pasadas = sum(r.get('validaciones_pasadas', 0) for r in resultados_validacion if r['encontrado'])

            print(f"\nValidaciones de campos:")
            print(f"  Total: {validaciones_totales}")
            print(f"  Pasadas: {validaciones_pasadas}")
            print(f"  Fallidas: {validaciones_totales - validaciones_pasadas}")
            print(f"  Porcentaje de éxito: {(validaciones_pasadas / validaciones_totales * 100):.1f}%")

        print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()

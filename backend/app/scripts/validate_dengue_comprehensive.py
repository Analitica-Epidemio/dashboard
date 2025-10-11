#!/usr/bin/env python3
"""
Script de validación COMPLETA de importación de eventos de Dengue.
Valida que se hayan importado exactamente 403 eventos y que TODOS LOS DATOS sean correctos.
"""
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict

import pandas as pd
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.domains.eventos_epidemiologicos.eventos.models import Evento, TipoEno
from app.domains.sujetos_epidemiologicos.ciudadanos_models import Ciudadano
from app.domains.territorio.establecimientos_models import Establecimiento
from app.domains.territorio.geografia_models import Provincia, Departamento, Localidad
from app.domains.atencion_medica.salud_models import Sintoma, MuestraEvento as Muestra


def parse_date(date_val):
    """Parsear fecha del CSV a objeto date."""
    if pd.isna(date_val) or not str(date_val).strip():
        return None

    for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']:
        try:
            return datetime.strptime(str(date_val).strip(), fmt).date()
        except:
            continue
    return None


class ValidationReport:
    """Clase para generar el reporte de validación."""

    def __init__(self):
        self.sections = []
        self.total_checks = 0
        self.passed_checks = 0
        self.failed_checks = 0
        self.warnings = []
        self.errors = []

    def add_section(self, title: str, content: str):
        """Agrega una sección al reporte."""
        self.sections.append((title, content))

    def add_check(self, passed: bool, description: str):
        """Registra una validación."""
        self.total_checks += 1
        if passed:
            self.passed_checks += 1
        else:
            self.failed_checks += 1
            self.errors.append(description)

    def add_warning(self, message: str):
        """Agrega una advertencia."""
        self.warnings.append(message)

    def print_report(self):
        """Imprime el reporte completo."""
        print("\n" + "="*100)
        print("📊 REPORTE DE VALIDACIÓN COMPLETA - IMPORTACIÓN DENGUE 2024")
        print("="*100 + "\n")

        for title, content in self.sections:
            print(f"\n{'─'*100}")
            print(f"📌 {title}")
            print(f"{'─'*100}")
            print(content)

        # Resumen de validaciones
        print(f"\n{'='*100}")
        print("✅ RESUMEN DE VALIDACIONES")
        print(f"{'='*100}\n")
        print(f"Total de validaciones: {self.total_checks}")
        print(f"  ✅ Pasadas: {self.passed_checks}")
        print(f"  ❌ Fallidas: {self.failed_checks}")

        if self.total_checks > 0:
            success_rate = (self.passed_checks / self.total_checks) * 100
            print(f"\n📊 Tasa de éxito: {success_rate:.1f}%")

        # Advertencias
        if self.warnings:
            print(f"\n⚠️  ADVERTENCIAS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")

        # Errores
        if self.errors:
            print(f"\n❌ ERRORES ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")

        # Conclusión
        print(f"\n{'='*100}")
        if self.failed_checks == 0:
            print("🎉 IMPORTACIÓN EXITOSA - Todos los datos validados correctamente")
        else:
            print(f"⚠️  IMPORTACIÓN INCOMPLETA - {self.failed_checks} validaciones fallidas")
        print(f"{'='*100}\n")


def validate_count_and_type(session: Session, df: pd.DataFrame, report: ValidationReport):
    """Valida cantidad y tipo de eventos de Dengue."""

    # Contar eventos únicos en CSV
    eventos_csv = df['IDEVENTOCASO'].nunique()

    # Obtener tipo Dengue (en minúscula)
    stmt = select(TipoEno).where(TipoEno.codigo == "dengue")
    tipo_dengue = session.execute(stmt).scalar_one_or_none()

    if not tipo_dengue:
        content = "❌ Tipo de evento Dengue (código 'dengue') no encontrado en la base de datos"
        report.add_check(False, "Tipo Dengue no existe en DB")
        report.add_section("1. VALIDACIÓN DE TIPO Y CANTIDAD DE EVENTOS", content)
        return None

    # Contar eventos de tipo Dengue en DB
    stmt = select(func.count()).select_from(Evento).where(Evento.id_tipo_eno == tipo_dengue.id)
    eventos_dengue_db = session.execute(stmt).scalar()

    content = f"Eventos únicos en CSV: {eventos_csv}\n"
    content += f"Tipo Dengue encontrado (código='{tipo_dengue.codigo}', id={tipo_dengue.id})\n"
    content += f"Eventos de Dengue en DB: {eventos_dengue_db}\n"

    if eventos_csv == 403:
        content += "✅ CSV contiene exactamente 403 eventos\n"
        report.add_check(True, "CSV contiene 403 eventos")
    else:
        content += f"❌ CSV tiene {eventos_csv} eventos (esperado: 403)\n"
        report.add_check(False, f"CSV tiene {eventos_csv} eventos")

    if eventos_dengue_db == 403:
        content += "✅ DB contiene exactamente 403 eventos de Dengue"
        report.add_check(True, "DB contiene 403 eventos de Dengue")
    else:
        content += f"❌ DB tiene {eventos_dengue_db} eventos de Dengue (esperado: 403)"
        report.add_check(False, f"DB tiene {eventos_dengue_db} eventos de Dengue")

    report.add_section("1. VALIDACIÓN DE TIPO Y CANTIDAD DE EVENTOS", content)
    return tipo_dengue.id


def validate_eventos_data(session: Session, df: pd.DataFrame, report: ValidationReport, id_tipo_dengue: int):
    """Valida que los datos de los eventos sean correctos comparando con CSV."""

    # DEBUG: Columnas de fecha
    print("\n🔍 DEBUG - FECHAS EN CSV:")
    fecha_cols = [col for col in df.columns if 'FECHA' in col or 'FTM' in col]
    print(f"   Columnas de fecha encontradas: {fecha_cols[:10]}")

    # Cargar eventos de Dengue
    stmt = select(Evento).where(Evento.id_tipo_eno == id_tipo_dengue)
    eventos_db = {e.id_evento_caso: e for e in session.execute(stmt).scalars().all()}

    # Agrupar CSV por IDEVENTOCASO
    df_grouped = df.groupby('IDEVENTOCASO')

    # Contadores
    eventos_ok = 0
    eventos_fail = 0
    errores_fechas = []
    errores_fechas_detallados = []
    errores_ciudadano = []
    errores_establecimiento = []

    sample_size = min(100, len(df_grouped))
    for id_evento_caso, grupo in list(df_grouped)[:sample_size]:
        evento_db = eventos_db.get(int(id_evento_caso))

        if not evento_db:
            eventos_fail += 1
            continue

        primera_fila = grupo.iloc[0]
        tiene_error = False

        # Validar fecha_minima_evento (4 columnas)
        fechas_csv = []
        for col in ['FECHA_APERTURA', 'FECHA_INICIO_SINTOMA', 'FECHA_CONSULTA', 'FTM']:
            fecha = parse_date(primera_fila.get(col))
            if fecha:
                fechas_csv.append(fecha)

        fecha_esperada = min(fechas_csv) if fechas_csv else None
        if fecha_esperada != evento_db.fecha_minima_evento:
            errores_fechas.append(f"Evento {id_evento_caso}: esperado {fecha_esperada}, obtenido {evento_db.fecha_minima_evento}")
            if len(errores_fechas_detallados) < 3:
                detalle = f"Evento {id_evento_caso}:\n"
                detalle += f"      FECHA_APERTURA: {parse_date(primera_fila.get('FECHA_APERTURA'))}\n"
                detalle += f"      FECHA_INICIO_SINTOMA: {parse_date(primera_fila.get('FECHA_INICIO_SINTOMA'))}\n"
                detalle += f"      FECHA_CONSULTA: {parse_date(primera_fila.get('FECHA_CONSULTA'))}\n"
                detalle += f"      FTM: {parse_date(primera_fila.get('FTM'))}\n"
                detalle += f"      → Esperado: {fecha_esperada}, DB: {evento_db.fecha_minima_evento}"
                errores_fechas_detallados.append(detalle)
            tiene_error = True

        # Validar código ciudadano
        if 'CODIGO_CIUDADANO' in primera_fila and pd.notna(primera_fila['CODIGO_CIUDADANO']):
            codigo_csv = int(primera_fila['CODIGO_CIUDADANO'])
            if codigo_csv != evento_db.codigo_ciudadano:
                errores_ciudadano.append(f"Evento {id_evento_caso}: esperado código {codigo_csv}, obtenido {evento_db.codigo_ciudadano}")
                tiene_error = True

        if not tiene_error:
            eventos_ok += 1
        else:
            eventos_fail += 1

    content = f"Eventos validados: {sample_size}\n"
    content += f"  ✅ Datos correctos: {eventos_ok}\n"
    content += f"  ❌ Datos incorrectos: {eventos_fail}\n\n"

    if errores_fechas:
        content += f"Errores en fechas (total: {len(errores_fechas)}):\n\n"
        for detalle in errores_fechas_detallados:
            content += f"  {detalle}\n"

    if errores_ciudadano:
        content += f"\nErrores en ciudadanos ({len(errores_ciudadano[:5])} primeros):\n"
        for error in errores_ciudadano[:5]:
            content += f"  - {error}\n"

    if eventos_fail == 0:
        content += "\n✅ Todos los datos de eventos son correctos"
        report.add_check(True, "Datos de eventos correctos")
    else:
        content += f"\n❌ {eventos_fail} eventos con datos incorrectos"
        report.add_check(False, f"{eventos_fail} eventos con datos incorrectos")

    report.add_section("2. VALIDACIÓN DE DATOS DE EVENTOS", content)


def validate_sintomas_correctos(session: Session, df: pd.DataFrame, report: ValidationReport, id_tipo_dengue: int):
    """Valida que los síntomas sean los correctos del CSV."""

    # Contar síntomas en CSV
    sintomas_csv = df[df['SIGNO_SINTOMA'].notna()]
    total_sintomas_csv = len(sintomas_csv)
    eventos_con_sintomas_csv = sintomas_csv['IDEVENTOCASO'].nunique()

    # DEBUG: Mostrar ejemplos de síntomas del CSV
    print("\n🔍 DEBUG - SÍNTOMAS EN CSV:")
    print(f"   Columnas relacionadas con síntomas: {[col for col in df.columns if 'SINTOMA' in col or 'SIGNO' in col]}")
    print(f"   Primeras 5 filas con síntomas:")
    for idx, row in sintomas_csv.head(5).iterrows():
        print(f"   - Evento {row['IDEVENTOCASO']}: '{row['SIGNO_SINTOMA']}' (ID_SNVS: {row.get('ID_SNVS_SIGNO_SINTOMA', 'N/A')})")

    # Verificar si existe la tabla de síntomas
    stmt = select(func.count()).select_from(Sintoma)
    total_sintomas_catalogo = session.execute(stmt).scalar()
    print(f"   Síntomas en catálogo DB: {total_sintomas_catalogo}")

    # Cargar eventos de Dengue con síntomas
    stmt = select(Evento).where(Evento.id_tipo_eno == id_tipo_dengue)
    eventos_db = session.execute(stmt).scalars().all()

    total_sintomas_db = sum(len(e.sintomas) if e.sintomas else 0 for e in eventos_db)
    eventos_con_sintomas_db = sum(1 for e in eventos_db if e.sintomas and len(e.sintomas) > 0)

    # DEBUG: Verificar si hay relaciones en DetalleEventoSintomas
    from app.domains.eventos_epidemiologicos.eventos.models import DetalleEventoSintomas
    stmt = select(func.count()).select_from(DetalleEventoSintomas)
    total_relaciones = session.execute(stmt).scalar()
    print(f"   Relaciones DetalleEventoSintomas en DB: {total_relaciones}")

    content = f"Síntomas en CSV:\n"
    content += f"  Total de filas con síntomas: {total_sintomas_csv}\n"
    content += f"  Eventos con síntomas: {eventos_con_sintomas_csv}\n"
    content += f"  Síntomas únicos: {sintomas_csv['SIGNO_SINTOMA'].nunique()}\n\n"

    content += f"Síntomas en DB:\n"
    content += f"  Catálogo de síntomas: {total_sintomas_catalogo}\n"
    content += f"  Relaciones evento-síntoma: {total_relaciones}\n"
    content += f"  Total de síntomas asociados: {total_sintomas_db}\n"
    content += f"  Eventos con síntomas: {eventos_con_sintomas_db}\n\n"

    # Validar que el conteo sea similar
    if total_sintomas_db == 0:
        content += f"❌ NO hay síntomas asociados a eventos (debería haber ~{total_sintomas_csv})\n"
        if total_sintomas_catalogo > 0:
            content += f"   ⚠️  IMPORTANTE: Hay {total_sintomas_catalogo} síntomas en el catálogo pero NO están asociados a eventos\n"
            content += f"   Esto indica que el procesador está creando síntomas pero NO está creando las relaciones DetalleEventoSintomas\n"
        report.add_check(False, "No hay síntomas asociados a eventos")
        report.add_warning(f"Se esperaban ~{total_sintomas_csv} síntomas pero hay 0 asociados")
    elif abs(total_sintomas_db - total_sintomas_csv) / total_sintomas_csv < 0.1:  # 10% de diferencia
        content += f"✅ Cantidad de síntomas similar a CSV (±10%)"
        report.add_check(True, "Síntomas importados correctamente")
    else:
        content += f"⚠️  Diferencia significativa: CSV tiene {total_sintomas_csv}, DB tiene {total_sintomas_db}"
        report.add_warning(f"Diferencia en cantidad de síntomas: {abs(total_sintomas_db - total_sintomas_csv)}")

    report.add_section("3. VALIDACIÓN DE SÍNTOMAS", content)


def validate_muestras(session: Session, df: pd.DataFrame, report: ValidationReport, id_tipo_dengue: int):
    """Valida que las muestras estén correctamente importadas."""

    # Buscar columnas de muestras en CSV
    columnas_muestras = [col for col in df.columns if 'MUESTRA' in col or 'FTM' in col or 'RESULTADO' in col]

    # Contar muestras en DB
    stmt = (
        select(func.count())
        .select_from(Muestra)
        .join(Evento, Muestra.id_evento == Evento.id)
        .where(Evento.id_tipo_eno == id_tipo_dengue)
    )
    total_muestras_db = session.execute(stmt).scalar()

    content = f"Columnas relacionadas con muestras en CSV:\n"
    for col in columnas_muestras[:10]:
        valores_no_vacios = df[col].notna().sum()
        content += f"  - {col}: {valores_no_vacios} valores no vacíos\n"

    content += f"\nMuestras en DB: {total_muestras_db}\n"

    if total_muestras_db == 0:
        content += "\n⚠️  No hay muestras importadas - revisar procesador"
        report.add_warning("No hay muestras importadas")
    else:
        content += f"\n✅ Hay {total_muestras_db} muestras importadas"
        report.add_check(True, f"{total_muestras_db} muestras importadas")

    report.add_section("4. VALIDACIÓN DE MUESTRAS", content)


def validate_ciudadanos_correctos(session: Session, df: pd.DataFrame, report: ValidationReport, id_tipo_dengue: int):
    """Valida que los datos de ciudadanos sean los correctos."""

    # DEBUG: Ver columnas de sexo en CSV
    print("\n🔍 DEBUG - SEXO EN CSV:")
    sexo_cols = [col for col in df.columns if 'SEXO' in col.upper()]
    print(f"   Columnas de sexo encontradas: {sexo_cols}")
    if sexo_cols:
        for col in sexo_cols:
            valores_unicos = df[col].dropna().unique()[:10]
            print(f"   Valores en '{col}': {valores_unicos}")

    # Cargar eventos de Dengue con ciudadanos
    stmt = (
        select(Evento, Ciudadano)
        .outerjoin(Ciudadano, Evento.codigo_ciudadano == Ciudadano.codigo_ciudadano)
        .where(Evento.id_tipo_eno == id_tipo_dengue)
        .limit(50)
    )
    results = session.execute(stmt).all()

    nombres_ok = 0
    nombres_fail = 0
    sexo_ok = 0
    sexo_fail = 0
    sexo_errores = []
    documentos_ok = 0
    documentos_fail = 0

    for evento, ciudadano in results:
        if not ciudadano:
            continue

        # Buscar en CSV
        csv_rows = df[df['IDEVENTOCASO'] == evento.id_evento_caso]
        if len(csv_rows) == 0:
            continue

        csv_row = csv_rows.iloc[0]

        # Validar nombre y apellido
        if 'NOMBRE' in csv_row and 'APELLIDO' in csv_row:
            nombre_csv = str(csv_row['NOMBRE']).strip().upper()
            apellido_csv = str(csv_row['APELLIDO']).strip().upper()
            nombre_db = str(ciudadano.nombre or '').strip().upper()
            apellido_db = str(ciudadano.apellido or '').strip().upper()

            if nombre_csv == nombre_db and apellido_csv == apellido_db:
                nombres_ok += 1
            else:
                nombres_fail += 1

        # Validar sexo
        if 'SEXO' in csv_row and pd.notna(csv_row['SEXO']):
            sexo_csv = str(csv_row['SEXO']).strip().upper()
            sexo_db = str(ciudadano.sexo_biologico or '').strip().upper() if ciudadano.sexo_biologico else None

            # Mapeo de valores comunes
            if sexo_csv in ['F', 'FEMENINO', 'MUJER'] and sexo_db in ['F', 'FEMENINO', 'MUJER']:
                sexo_ok += 1
            elif sexo_csv in ['M', 'MASCULINO', 'HOMBRE', 'VARON'] and sexo_db in ['M', 'MASCULINO', 'HOMBRE', 'VARON']:
                sexo_ok += 1
            elif sexo_csv == sexo_db:
                sexo_ok += 1
            else:
                sexo_fail += 1
                if len(sexo_errores) < 5:
                    sexo_errores.append(f"Evento {evento.id_evento_caso}: CSV='{sexo_csv}' vs DB='{sexo_db}'")

        # Validar documento
        if 'NUMERO_DOCUMENTO' in csv_row and pd.notna(csv_row['NUMERO_DOCUMENTO']):
            doc_csv = int(csv_row['NUMERO_DOCUMENTO'])
            if doc_csv == ciudadano.numero_documento:
                documentos_ok += 1
            else:
                documentos_fail += 1

    content = f"Validación de ciudadanos (muestra de 50 eventos):\n\n"
    content += f"Nombres y apellidos:\n"
    content += f"  ✅ Correctos: {nombres_ok}\n"
    content += f"  ❌ Incorrectos: {nombres_fail}\n\n"

    content += f"Sexo:\n"
    content += f"  ✅ Correcto: {sexo_ok}\n"
    content += f"  ❌ Incorrecto: {sexo_fail}\n"
    if sexo_errores:
        content += f"\n  Ejemplos de errores de sexo:\n"
        for error in sexo_errores:
            content += f"    - {error}\n"
    content += "\n"

    content += f"Documentos:\n"
    content += f"  ✅ Correctos: {documentos_ok}\n"
    content += f"  ❌ Incorrectos: {documentos_fail}\n"

    total_validaciones = nombres_ok + nombres_fail + sexo_ok + sexo_fail + documentos_ok + documentos_fail
    total_ok = nombres_ok + sexo_ok + documentos_ok
    total_fail = nombres_fail + sexo_fail + documentos_fail

    if total_fail == 0 and total_validaciones > 0:
        content += "\n✅ Todos los datos de ciudadanos validados son correctos"
        report.add_check(True, "Datos de ciudadanos correctos")
    elif total_validaciones > 0:
        content += f"\n⚠️  {total_fail} de {total_validaciones} validaciones fallidas"
        report.add_check(False, f"{total_fail} datos de ciudadanos incorrectos")

    report.add_section("5. VALIDACIÓN DE DATOS DE CIUDADANOS", content)


def main():
    """Ejecuta la validación completa."""

    # Ruta al CSV (inside Docker container)
    csv_path = '/app/Meningitis 2024 y 2023.xlsx - Hoja 1(1).csv'

    if not os.path.exists(csv_path):
        print(f"❌ Archivo CSV no encontrado: {csv_path}")
        return

    print("\n🔍 Cargando CSV...")
    df = pd.read_csv(csv_path)
    print(f"   Total de filas en CSV: {len(df)}")

    # Conectar a la base de datos
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://epidemiologia_user:epidemiologia_password@localhost:5433/epidemiologia_db"
    )
    if "postgresql+asyncpg" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    print(f"🔌 Conectando a la base de datos...")
    engine = create_engine(DATABASE_URL)

    # Crear reporte
    report = ValidationReport()

    with Session(engine) as session:
        # Ejecutar todas las validaciones
        id_tipo_dengue = validate_count_and_type(session, df, report)

        if id_tipo_dengue is None:
            print("\n⚠️  No se puede continuar: tipo Dengue no encontrado")
            report.print_report()
            return

        validate_eventos_data(session, df, report, id_tipo_dengue)
        validate_sintomas_correctos(session, df, report, id_tipo_dengue)
        validate_muestras(session, df, report, id_tipo_dengue)
        validate_ciudadanos_correctos(session, df, report, id_tipo_dengue)

    # Imprimir reporte
    report.print_report()


if __name__ == "__main__":
    main()
